# Design & Implementation of Event-Driven Microservices Architecture using MiniStack (Proof of Concept)

Sebuah *Proof of Concept* (PoC) sistem backend e-commerce berskala enterprise menggunakan arsitektur **Serverless** dan **Event-Driven Architecture (EDA)**. Project ini menerapkan pola **Choreography Fan-Out** untuk memproses siklus hidup pesanan (*order lifecycle*) secara asinkronus dan *fault-tolerant*, disimulasikan sepenuhnya secara lokal menggunakan **MiniStack**.

## 🚀 Masalah yang Diselesaikan (The "Why")

Pada arsitektur monolitik konvensional, proses *checkout* sering mengalami *bottleneck* (blocking I/O) karena klien harus menunggu proses pembayaran, kalkulasi inventaris, hingga pengiriman email selesai dalam satu siklus *request-response* yang sinkronous. 

Project ini memisahkan batas tersebut secara ketat:
* **Synchronous Path (< 50ms):** Klien mengirim order, sistem mencatat data mentah dengan status `PENDING`, dan langsung melakukan *early return* berupa status `202 Accepted`.
* **Asynchronous Path (Background):** Komputasi berat (alokasi inventaris, pemrosesan transaksi) dan integrasi pihak ketiga (email notifikasi via Amazon SES) didelegasikan sepenuhnya ke jaringan pipa asinkronus di *background* memanfaatkan antrean pesan dan *database streams*.

---

## 🏛️ Arsitektur Sistem & Aliran Data

Sistem ini menerapkan prinsip **CQRS** (pemisahan jalur tulis dan baca) serta pola **Choreography Fan-Out** berbasis *Change Data Capture* (CDC).

```mermaid
graph LR
    %% Pengaturan Gaya/Warna
    classDef client fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef lambda fill:#ff9900,stroke:#fff,stroke-width:2px,color:#fff;
    classDef database fill:#146eb4,stroke:#fff,stroke-width:2px,color:#fff;
    classDef queue fill:#cc0000,stroke:#fff,stroke-width:2px,color:#fff;
    classDef email fill:#009900,stroke:#fff,stroke-width:2px,color:#fff;

    %% Komponen Sisi Depan / Ingestion
    Klien((Client / Frontend)):::client
    
    subgraph Synchronous_Boundary [Synchronous Boundary - Low Latency]
        CreateOrder["Lambda: CreateOrder"]:::lambda
    end

    %% Komponen Database & CDC
    subgraph Data_Layer [Data & Stream Layer]
        DynamoDB[("DynamoDB: Orders Table")]:::database
        DBStream{{"DynamoDB Stream: CDC"}}:::database
    end

    %% Pipa Asinkronus Background
    subgraph Asynchronous_Boundary [Asynchronous Boundary - Decoupled Core]
        StreamFilter["Lambda: StreamFilter"]:::lambda
        SQS[["SQS: order-processing-queue"]]:::queue
        Worker["Lambda: Worker"]:::lambda
        Notification["Lambda: NotificationLambda"]:::lambda
        SES["Amazon SES: Sandbox Server"]:::email
    end

    %% Jalur CQRS Read Path
    subgraph CQRS_Read_Path [CQRS Read-Only Path]
        GetOrder["Lambda: GetOrder"]:::lambda
    end

    %% Aliran Data Sinkronous (Command Path)
    Klien -->|1. HTTP POST Payload| CreateOrder
    CreateOrder -->|2. PutItem status: PENDING| DynamoDB
    CreateOrder -.->|3. Early Return 202 Accepted| Klien

    %% Aliran Data Asinkronus (Change Data Capture & Queue)
    DynamoDB --->|4. Capture Mutated State| DBStream
    
    %% Jalur Koki Utama (Worker)
    DBStream --->|5a. Filter: eventName==INSERT & status==PENDING| StreamFilter
    StreamFilter -->|6. Push Message| SQS
    SQS -->|7. Trigger Batch Control Size=1| Worker
    Worker ===>|8. UpdateItem status: COMPLETED| DynamoDB

    %% Jalur Jalur Fan-Out Notifikasi
    DBStream --->|5b. Filter: eventName==MODIFY & status==COMPLETED| Notification
    Notification -->|9. Trigger send_email API| SES
    SES -.->|10. Asynchronous Email Sent| Klien

    %% Jalur Polling Status (Query Path)
    Klien ---->|Check Order Status| GetOrder
    GetOrder --->|Fetch Terminal State| DynamoDB
