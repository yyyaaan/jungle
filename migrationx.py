from dataclasses import field

from rsa import verify


file_name = "index"

### Coursera courses summaried
### https://bulkresizephotos.com/en?quality=0.91&type=width&value=300

the_str = """
name
institute
credential
logo (fa-icon)
type (A or B)
courses (names)


AI for Medicine <small> Professional Certificate</small>
DeepLearning.AI
WKRFNRRR8YYY
<i class="fas fa-capsules"></i>
A
AI for Medical Diagnosis
AI for Medical Prognosis
AI For Medical Treatment


IBM AI Engineering <small> Professional Certificate</small>
IBM
5VNYW898L2X9
<i class="fas fa-flag-checkered"></i>
A
Machine Learning with Python
Scalable Machine Learning on Big Data using Apache Spark
Introduction to Deep Learning & Neural Networks with Keras
Deep Neural Networks with PyTorch
Building Deep Learning Models with TensorFlow
AI Capstone Project with Deep Learning


DeepLearning.AI TensorFlow Developer <small> Professional Certificate</small>
DeepLearning.AI
D3ATD54NQQ74
<i class="far fa-lightbulb"></i>
A
Introduction to TensorFlow for Artificial Intelligence, Machine Learning, and Deep Learning
Convolutional Neural Networks in TensorFlow
Natural Language Processing in TensorFlow
Sequences, Time Series and Prediction


Google Data Analytics <small> Professional Certificate</small>
Google
3B9PVVBSANNS
<i class="fab fa-google"></i>
A
Foundations: Data, Data, Everywhere
Ask Questions to Make Data-Driven Decisions
Prepare Data for Exploration
Process Data from Dirty to Clean
Analyze Data to Answer Questions
Share Data Through the Art of Visualization
Data Analysis with R Programming
Google Data Analytics Capstone: Complete a Case Study


Fundamentals of Parallelism on Intel Architecture
Intel
D3X88XPBDWQC
<i class="fas fa-microchip"></i>
C
Vectorization, OpenMP, Memory Optimization, Clusters and MPI


Advanced Machine Learning on Google Cloud
Google Cloud
H7EKZL2N3BKR
<i class="fab fa-cloudversify"></i>
B
End-to-End Machine Learning with TensorFlow on GCP
Production Machine Learning Systems
Image Understanding with TensorFlow on GCP
Sequence Models for Time Series and Natural Language Processing
Recommendation Systems with TensorFlow on GCP


Machine Learning for Trading
Google Cloud, New York Institute of Finance
ZDZNN7YTWMU4
<i class="fas fa-chart-line"></i>
B
Introduction to Trading, Machine Learning & GCP
Using Machine Learning in Trading and Finance
Reinforcement Learning for Trading Strategies


Machine Learning with TensorFlow on Google Cloud Platform
Google Cloud
X6SMHCN6VM73
<i class="fas fa-layer-group"></i>
B
How Google does Machine Learning
Launching into Machine Learning
Introduction to TensorFlow
Feature Engineering
Art and Science of Machine Learning


Deep Learning
DeepLearning.AI
629H5B983QTX
<i class="fas fa-grip-vertical"></i>
B
Neural Networks and Deep Learning
Improving Deep Neural Networks: Hyperparameter Tuning, Regularization and Optimization
Structuring Machine Learning Projects
Convolutional Neural Networks
Sequence Models


Applied Data Science with Python
University of Michigan
FXFS2CDJUK2Q
<i class="fab fa-python"></i>
B
Introduction to Data Science in Python
Applied Plotting, Charting & Data Representation in Python
Applied Machine Learning in Python
Applied Text Mining in Python
Applied Social Network Analysis in Python
"""

generated_html = ""
fixtures = []


for i, the_block in enumerate(the_str.split("\n\n\n")[1:]):
    fields = the_block.split("\n")

    fixtures.append({
        "model": "yancv.cvcert",
        "pk": fields[0].split("<small>")[0].rstrip(),
        "fields": {
            "display_order": i,
            "enabled": True,
            "icon_tag": fields[3],
            "title_extra": ("Professional Certificate" if "Professional" in fields[0] else ""),
            "issuer": fields[1],
            "courses": "|".join(fields[5:]),
            "details": "",
            "imgname": f"{fields[2]}.jpg",
            "verify_link": f"http://coursera.org/verify/professional-cert/{fields[2]}"
        }
    })

from json import dumps

print(dumps(fixtures, indent=4))