
<div align="center">

<h2 align="center">Real Time Analytics of Disease Progression</h2>

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

This project focuses on real time analytics of the Disease progression. It shows the analytics for mainly 3 diseases:- Covid, RSV and Influenza over the years. The data ingested through the Apache Kafka pipeline onto the Timeseries database InfluxDB. I am using Python Darts library for the time series prediction. I am using React in the front End and Django in the backend

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* <a href="https://spark.apache.org/">Apache Kafka </a>
* <a href="https://solr.apache.org/"> InfluxDB</a>
* <a href="https://solr.apache.org/"> Darts</a>
* <a href="https://solr.apache.org/"> React</a>
* <a href="https://solr.apache.org/"> Django</a>

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
2. Start the front end using:
   ```sh
   npm build
   npm run dev
   ```
3. Start the Apache Kafka and create a topic called timeseries-pred
   ```sh
    bin/zookeeper-server-start.sh config/zookeeper.properties
    bin/kafka-server-start.sh config/server.properties
    bin/kafka-topics.sh --create --topic covid-data --bootstrap-server localhost:9092
   ```
4. Start the InfluxDB database:
4. Start the backend application 
   ```sh
   python manage.py runserver
   ``` 

## Contact

Gundeti Shiva Hari - u1460836@utah.edu 


<p align="right">(<a href="#readme-top">back to top</a>)</p>

