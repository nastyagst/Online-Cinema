# Online Cinema API



A high-performance RESTful API for an Online Cinema platform, built with **FastAPI** and deployed on **AWS**.



## Live Demo

The API documentation is available at: [http://13.62.248.27:8002/docs](http://13.62.248.27:8002/docs)



## Key Features

* **User Authentication:** JWT-based login and registration.

* **Movie Management:** CRUD operations for movies, genres, stars, and directors.

* **Shopping Cart & Orders:** Full cycle from adding to cart to placing an order.

* **Stripe Integration:** Automated payment processing with **Webhooks**.

* **Background Tasks:** Sending emails via **Celery** and **Redis**.

* **Deployment:** Containerized with **Docker** and automated via **GitHub Actions (CI/CD)**.



## Tech Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy (Async)

- **Database:** PostgreSQL

- **Task Queue:** Celery + Redis

- **Payments:** Stripe API

- **Infrastructure:** Docker, Docker Compose, AWS EC2



## API Documentation

All endpoints are documented using **Swagger UI**.

- **Custom Endpoints:** Detailed docstrings explain parameters and actions for specialized routes like Stripe webhooks and order processing.

- **Security:** Protected routes require a Bearer Token (JWT).



##  Testing & Demo Credentials

### 1. Pre-created Accounts
You can test protected routes using these credentials:
* **Admin/Moderator:** `admin@example.com` / `adminAdmin1@`
* **Regular User:** `user@test.com` / `UserPass123!`

### 2. Stripe Test Card (Sandbox)
To test the checkout process, use the standard Stripe test card:
* **Card Number:** `4242 4242 4242 4242`
* **Expiry:** Any future date (e.g., `12/26`)
* **CVC:** `123`

### 3. Running Tests
The project is covered by **Pytest**. To execute tests within the Docker container:
```bash
docker exec -it online_cinema_app pytest