<div align="center">

# ☁️ Smart Cloud Inventory

**A production-grade inventory, point-of-sale, and sales analytics platform — built as a hybrid desktop + web application.**

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-Frontend-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Electron](https://img.shields.io/badge/Electron-Desktop-47848F?logo=electron&logoColor=white)](https://www.electronjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-CC2927)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

[Features](#-features) • [Screenshots](#-screenshots) • [Architecture](#-architecture) • [Setup](#-local-setup) • [API](#-api-reference)

</div>

---

## 📋 Overview

**Smart Cloud Inventory** is a full-stack inventory management and point-of-sale system designed for small-to-mid-sized retail businesses — cafés, electronics shops, and general stores. It combines a modern web dashboard with a native desktop client (via Electron), all backed by a single FastAPI service and a shared database, so stock levels, sales, and analytics stay perfectly in sync across both.

The project was built to demonstrate a genuinely full-stack skill set: a typed REST API with authentication and role handling, transactional business logic (stock decrementing, invoice generation), a real-time analytics dashboard, and a desktop packaging pipeline — not just a CRUD demo.

---

## ✨ Features

- 🔐 **JWT Authentication** with role-based access (Admin / Staff)
- 📦 **Product & Category Management** — full CRUD with SKU/barcode search
- 📷 **Camera Barcode Scanning** for fast product lookup at checkout
- ⚠️ **Low-Stock Alerts** with configurable thresholds
- 🛒 **POS Checkout** — cart management, cash/card payments, discounts
- 🔄 **Transactional Stock Updates** — inventory decrements atomically on sale
- 🧾 **PDF Invoice Generation** for every completed sale
- 📊 **Live Analytics Dashboard** — revenue KPIs, daily sales trend, top-selling products, category breakdown
- 🖥️ **Cross-Platform Desktop App** via Electron, backed by the same API as the web dashboard

---

## 🖼 Screenshots

<div align="center">

| Overview Dashboard | Sales Analytics |
|---|---|
| ![Overview](docs/screenshots/dashboard.png) | ![Analytics](docs/screenshots/analytics.png) |

| Inventory Management | POS Terminal |
|---|---|
| ![Inventory](docs/screenshots/inventory.png) | ![POS](docs/screenshots/pos.png) |

</div>

> Screenshots are stored in [`docs/screenshots/`](docs/screenshots/). Replace the placeholders above with current captures before publishing.

---

## 🏗 Architecture

```text
.
├── backend/
│   └── app/
│       ├── api/routes/        # Auth, inventory, sales, analytics REST endpoints
│       ├── core/               # Settings, JWT & password security
│       ├── db/                 # SQLAlchemy engine and sessions
│       ├── models/             # User, category, product, sale models
│       └── schemas/            # Pydantic API contracts
├── frontend/
│   ├── electron/               # Secure Electron main/preload processes
│   └── src/
│       ├── context/             # Authentication state
│       ├── pages/               # Auth, dashboard, inventory, POS, analytics
│       └── lib/                 # API client and invoice download helpers
└── package.json                 # Workspace + desktop dev commands
```

**How it fits together:** the React (Vite) frontend renders both in the browser and inside Electron's renderer process, talking to a single FastAPI backend over REST. Electron's main process handles native window management and secure IPC via a preload script, while all business logic — auth, stock, sales, analytics — lives entirely in the backend, so the web and desktop clients are always looking at the same source of truth.

---

## 🧰 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide React, Recharts, html5-qrcode |
| **Desktop** | Electron |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy 2, Pydantic |
| **Database** | SQLite (default) — MySQL or PostgreSQL-compatible via connection URL |
| **Auth & Security** | JWT, Passlib (bcrypt) |
| **PDF Generation** | ReportLab |

---

## 🚀 Local Setup

### Prerequisites

- Node.js 20+
- npm 10+
- Python 3.11+

### Installation

```powershell
npm install
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

### Configuration

SQLite is used by default — no extra setup required:

```env
DATABASE_URL=sqlite:///./inventory.db
```

To use MySQL instead:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/inventory
```

> ⚠️ Set a strong, unique `JWT_SECRET_KEY` before deploying to any non-development environment.

### Running the app

```powershell
npm run dev
```

This orchestrates all three processes together. To run them individually instead:

```powershell
npm run dev:api        # FastAPI backend (Uvicorn)
npm run dev:frontend   # Vite dev server
npm run dev:electron   # Electron desktop shell
```

The Electron main process loads the Vite dev server during development and the built `frontend/dist` bundle once packaged for production.

---

## 📡 API Reference

All endpoints except `health` and `auth` require an `Authorization: Bearer <token>` header.

| Area | Endpoint |
|---|---|
| **Health** | `GET /api/v1/health` |
| **Auth** | `POST /api/v1/auth/register` · `POST /api/v1/auth/login` · `GET /api/v1/auth/me` |
| **Categories** | `GET/POST /api/v1/categories` · `PUT/DELETE /api/v1/categories/{id}` |
| **Products** | `GET/POST /api/v1/products` · `PUT/DELETE /api/v1/products/{id}` · `GET /api/v1/products/low-stock` |
| **Sales** | `POST /api/v1/sales` · `GET /api/v1/sales/{id}/invoice` |
| **Analytics** | `GET /api/v1/analytics/summary` · `GET /api/v1/analytics/sales-trend?days=7` · `GET /api/v1/analytics/top-products` · `GET /api/v1/analytics/category-breakdown` |

Interactive API docs are available at `/docs` (Swagger UI) once the backend is running.

---

## 🗺 Roadmap

Planned enhancements for future releases:

- [ ] Customer management (CRM) with purchase history and loyalty points
- [ ] Supplier management and purchase-order restock workflow
- [ ] Role-based UI restrictions for Admin / Manager / Cashier
- [ ] In-app notification center for low-stock and daily summaries
- [ ] Global command palette (`Ctrl+K`) for fast navigation
- [ ] Audit/activity log for key user actions
- [ ] Bulk CSV import/export for inventory
- [ ] Barcode label generation for new products

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Built as a full-stack portfolio project demonstrating end-to-end product development — from database schema to desktop packaging.

</div>