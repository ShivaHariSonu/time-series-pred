
<div align="center">

<h2 align="center">U Health Forecast Hub</h2>

  <p align="center">
    <a href="https://github.com/ShivaHariSonu/time-series-pred"><strong>Explore the docs »</strong></a>
    <br />
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#how-to-run">How to run</a></li>
        <li><a href="#code-execution">Code Execution</a></li>
      </ul>
    </li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This project focuses on real time analytics of the Disease progression. It shows the analytics for mainly 3 diseases:- Covid, RSV and Influenza over the years. The data ingested to the PostgreSQL. I am using Python Darts library for the time series prediction. I am using React in the front End and Django in the backend

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* <a href="https://www.postgresql.org/"> PostgreSQL</a>
* <a href="https://unit8co.github.io/darts/"> Darts</a>
* <a href="https://react.dev/"> React</a>
* <a href="https://www.djangoproject.com/"> Django</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started
To get a local copy up and running, follow these simple steps.
### Installation
1. Clone the repo
   ```sh
   git clone https://github.com/ShivaHariSonu/time-series-pred.git
### How to run
Follow these steps to get your development environment set up:
1. Change to the project directory as shown below:
   ```sh
   cd time-series-pred/front-end/
2. Make sure you install all the necessary dependencies needed for the project
3. Start the front end using:
   ```sh
   npm build
   npm run dev
   ```
4. Make sure you start postgres database in your local system.

5. In another tab, open the backend directory as shown below
   ```sh
   cd time-series-pred/back-end/
   ```
6. After installing all the necessary dependencies (I have added requirements.txt file. You can install the dependencies from there in your virtual environment), run the initial migrations
   ```sh
   python manage.py migrate
   ```
7. Run the development Server
   ```sh
   python manage.py runserver
   ```
8. Open the browser at localhost:5173

## Contact

Gundeti Shiva Hari - u1460836@utah.edu 


<p align="right">(<a href="#readme-top">back to top</a>)</p>

