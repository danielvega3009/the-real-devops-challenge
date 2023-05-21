Challenge 1. The API returns a list instead of an object
As you can see, the API returns a list in the two exposed endpoints:

/api/v1/restaurant: Returns a list containing all the restaurants.
/api/v1/restaurant/{id}: Returns a list with a single restaurant that match the id path parameter.
We want to fix the second endpoint. Return a json object instead of a json array if there is a match or a http 204 status code if no match found.

For this purpose I have modified:
@app.route("/api/v1/restaurant/<id>")
def restaurant(id):
    restaurants = find_restaurants(mongo, id)
    return jsonify(restaurants)
	
por 
@app.route("/api/v1/restaurant/<id>")
def restaurant(id):
    restaurant = mongo.db.restaurant.find_one({"_id": ObjectId(id)})
    if restaurant is None:
        abort(204)
    return jsonify(restaurant)


where I check if there is data or not to return a 204 with the abort function, and 
I have used the jsonify function to be able to convert the returned response into a
json


Challenge 2. Test the application in any cicd system
CICD

As a good devops engineer, you know the advantages of running tasks in an automated way. There are some cicd systems that can be used to make it happen. Choose one, travis-ci, gitlab-ci, circleci... whatever you want. Give us a successful pipeline.

I have no experience in generating pipelines, so I have researched and developed the following pipeline, based on how I would do it with the Jenkins tool:

pipeline {
    agent any

    stages {
        stage('Checkout') { //comprobamos si existe el repo y lo descargamos
            steps {
                git 'https://github.com/danielvega3009/the-real-devops-challenge'
				git clone https://github.com/danielvega3009/the-real-devops-challenge.git
            }
        }

        stage('Setup') { //configure the environment in the agent
            steps {
                sh 'python3 -m venv venv'
                sh 'source venv/bin/activate'
                sh 'pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') { //we install the dependencies that come in the requirements.txt
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Testing') { //we test with tox, which already comes in the project
            steps {
                sh 'tox'
            }
        }

        stage('Create Release') { //we generate release in git
            steps {
                sh 'git tag -a v1.0 -m "Release v1.0"'
                sh 'git push origin v1.0'
            }
        }

        stage('Deployment') {// in this step we deploy the app, for lack of knowledge I do not have clear that commands are used here, but I imagine that it will be something like copying the files in the corresponding environment.
            steps {
                // Agrega aquí los pasos para desplegar y operar con la aplicación
            }
        }
    }
}

Challenge 3. Dockerize the APP
DockerPython

What about containers? As this moment (2018), containers are a standard in order to deploy applications (cloud or in on-premise systems). So the challenge is to build the smaller image you can. Write a good Dockerfile :)
# Use the base image of Python 3.6.8
FROM python:3.6.8

# Set the working directory inside the container
WORKDIR /app

# Copy the application files to the container
COPY . /app

# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port if necessary
EXPOSE 8000

# Set the container start command
CMD ["python", "app.py"]


Challenge 4. Dockerize the database
DockerMongo

We need to have a mongodb database to make this application run. So, we need a mongodb container with some data. Please, use the restaurant dataset to load the mongodb collection before running the application.

The loaded mongodb collection must be named: restaurant. Do you have to write code or just write a Docker file?
# Use the base image of MongoDB 6.0.6
FROM mongo:6.0.6

# Copy restaurant.json file to /docker-entrypoint-initdb.d directory of the container
COPY restaurant.json /docker-entrypoint-initdb.d/

# Set optional environment variables for MongoDB
ENV MONGO_INITDB_ROOT_USERNAME=admin \
    MONGO_INITDB_ROOT_PASSWORD=password

# Expose the MongoDB port
EXPOSE 27017

# Set the container start command (provided by the base image)
CMD ["mongod"]


Challenge 5. Docker Compose it
Docker Compose

Once you've got dockerized all the API components (python app and database), you are ready to make a docker-compose file. KISS.
I have no experience in dockers or dockercompose , but researching I have been able to reach this solution, in which will allow us to deploy the 2 containers created previously:
version: '3
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile-app (docker image created earlier)
    ports:
      - 8000:8000 (port to expose the app).
    depends_on:
      - db (depends on db which is the mongodb database).
  db:
    build:
      context: .
      dockerfile: Dockerfile-mongodb
    ports:
      - 27017:27017 (port where we will expose the dbdd).
    volumes:
      - ./data:/data/db (volume where restaurant data will persist).

To execute: docker-compose up
note: have the dockerfile in the same directory of dockercompose

Final Challenge. Deploy it on kubernetes
Kubernetes

If you are a container hero, an excellent devops... We want to see your expertise. Use a kubernetes system to deploy the API. We recommend you to use tools like minikube or microk8s.

Write the deployment file (yaml file) used to deploy your API (python app and mongodb).

I have no experience in kubernetes, the following deployment.yaml I have made based on documentation on the internet, the deployment did not work for me, but the resulting script is as follows:
apiVersion: apps/v1
kind: Deployment (in this part we will deploy the python app)
metadata:
  name: app-deployment
spec:
  replicas: 3 (we will make 3 replicas to ensure availability and fault tolerance)
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers: (run the container on port 8000)
        - name: app
          image: python:3.6.8
          ports:
            - containerPort: 8080
		  env:
			- name: MONGO_URI
			- value: mongodb://mongodb:27017/restaurant
---
apiVersion: v1 (in this part we expose the container as a service to be able to access by http)
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000 (will be exposed on port 80)
  type: LoadBalancer (type LoadBalancer so that kubernetes directs the traffic to the replica with less load)
---
apiVersion: apps/v1 (this part is in charge of deploying the mongodb bbdd)
kind: Deployment
metadata:
  name: db-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-db
  template:
    metadata:
      labels:
        app: my-db
    spec:
      containers:
        - name: db
          image: mongo:6.0.6
          ports:
            - containerPort: 27017
          volumeMounts:
            - name: db-data
              mountPath: /data/db
      volumes:
        - name: db-data
          emptyDir: {}

To run the deployment:
kubectl apply -f deployment.yaml

To check the status of the deployments use the command:
kubectl get deployments

and the status of the services with:
kubectl get services



