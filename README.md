# College Admission Digiform Demo

<div style="text-align: justify">
DigiForm is an AI-assisted digital form-filling solution developed to address the significant challenges faced in India’s form-filling processes. These challenges include low literacy and digital literacy rates, limited internet and user-friendly platform access, language barriers, and complex documentation requirements. Modelled after the successful DigiLocker initiative, DigiForm aims to simplify and standardize digital form processing, enhance data accuracy, and improve service delivery through AI.
</div>

<br>


<div style="text-align: justify">
Our solution operates on core design principles: speed to ensure quick and user-friendly form filling, accuracy with validation checks to reduce errors, privacy with compliance to data protection regulations, and access by providing multilingual support and inclusive user interfaces. DigiForm mainly benefits individuals with low to moderate literacy levels, those who find form filling tedious or challenging, and people requiring assistance due to disabilities.
</div>

<br>

<div style="text-align: justify">
By utilizing various information formats such as text, speech, and images, DigiForm minimizes the need for extensive text input, creating a more inclusive and rapid form-filling experience. Through AI, we strive to make form-filling more accessible, efficient, and reliable for everyone, ultimately improving access to essential services in India.
</div>

<br>

## Demo Video

https://github.com/aashnijoshi/DigiForm-Aashni/assets/41504377/c89d546f-fdfc-4237-a205-6232e2d3b5a3

<br>

## Run Instructions

To run the College Admission Digiform Demo, follow these steps:

### Prerequisites

Make sure you have the following installed:
- Docker
- Docker Compose

### Steps

1. **Clone the repository**:

   ```sh
   git clone https://github.com/aashnijoshi/DigiForm-CollegeApp.git
   cd DigiForm-CollegeApp
   ```

2. **Create a `.env` file** in the project root with the following content (replace placeholders with your actual values):

   ```plaintext
   DATABASE_URL=postgresql://postgres:password@db:5432/registration
   REDIS_URL=redis://redis:6379/0
   REDIS_URL_RATE_LIMITS=redis://redis:6379/1
   OPENAI_API_KEY=your_openai_api_key
   PORT=5001
   ```

3. **Build and run the Docker containers**:

   ```sh
   docker-compose up --build -d
   ```

4. **Access the application**:

   Open your web browser and navigate to `http://localhost:5001` (or the port specified in your `.env` file).

### Troubleshooting

- If you encounter any issues, check the logs of the services using:

  ```sh
  docker-compose logs web
  docker-compose logs db
  docker-compose logs redis
  ```

- Ensure that your environment variables in the `.env` file are correctly set.
```

This README now assumes that the `wait-for-it.sh` script is already included in the repository and focuses only on the essential steps needed to set up and run the application.
