Challenge 1. The API returns a list instead of an object
As you can see, the API returns a list in the two exposed endpoints:

/api/v1/restaurant: Returns a list containing all the restaurants.
/api/v1/restaurant/{id}: Returns a list with a single restaurant that match the id path parameter.
We want to fix the second endpoint. Return a json object instead of a json array if there is a match or a http 204 status code if no match found.

Para ello he modificado:
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


donde compruebo si hay datos o no para devolver un 204 con la función abort, y 
he usado la función jsonify para poder convertir la respuesta devuelta en un objeto
json


Challenge 2. Test the application in any cicd system
CICD

As a good devops engineer, you know the advantages of running tasks in an automated way. There are some cicd systems that can be used to make it happen. Choose one, travis-ci, gitlab-ci, circleci... whatever you want. Give us a successful pipeline.

No tengo experiencia en la generación de pipelines, por lo que he investigado y he desarrollado la siguiente pipeline, basandome en cómo lo haría con la herramienta Jenkins:

pipeline {
    agent any

    stages {
        stage('Checkout') { //comprobamos si existe el repo y lo descargamos
            steps {
                git 'https://github.com/danielvega3009/the-real-devops-challenge'
				git clone https://github.com/danielvega3009/the-real-devops-challenge.git
            }
        }

        stage('Setup') { //configuramos el entorno en el agente
            steps {
                sh 'python3 -m venv venv'
                sh 'source venv/bin/activate'
                sh 'pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') { //instalamos las dependencias que nos vienen en el requirements.txt
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Testing') { //testeamos con tox, la cual ya viene en el proyecto
            steps {
                sh 'tox'
            }
        }

        stage('Create Release') { //generamos release en git
            steps {
                sh 'git tag -a v1.0 -m "Release v1.0"'
                sh 'git push origin v1.0'
            }
        }

        stage('Deployment') {// en este paso desplegamos la app, por falta de conocimientos no tengo claro que comandos se usan aquí, pero imagino
		que será algo como copiar los ficheros en el entorno correspondiente
            steps {
                // Agrega aquí los pasos para desplegar y operar con la aplicación
            }
        }
    }
}

Challenge 3. Dockerize the APP
DockerPython

What about containers? As this moment (2018), containers are a standard in order to deploy applications (cloud or in on-premise systems). So the challenge is to build the smaller image you can. Write a good Dockerfile :)
# Utilizar la imagen base de Python 3.6.8
FROM python:3.6.8

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos de la aplicación al contenedor
COPY . /app

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto si es necesario
EXPOSE 8000

# Establecer el comando de inicio del contenedor
CMD ["python", "app.py"]


Challenge 4. Dockerize the database
DockerMongo

We need to have a mongodb database to make this application run. So, we need a mongodb container with some data. Please, use the restaurant dataset to load the mongodb collection before running the application.

The loaded mongodb collection must be named: restaurant. Do you have to write code or just write a Docker file?
# Utilizar la imagen base de MongoDB 6.0.6
FROM mongo:6.0.6

# Copiar el archivo restaurant.json al directorio /docker-entrypoint-initdb.d del contenedor
COPY restaurant.json /docker-entrypoint-initdb.d/

# Establecer variables de entorno opcionales para MongoDB
ENV MONGO_INITDB_ROOT_USERNAME=admin \
    MONGO_INITDB_ROOT_PASSWORD=password

# Exponer el puerto de MongoDB
EXPOSE 27017

# Establecer el comando de inicio del contenedor (proporcionado por la imagen base)
CMD ["mongod"]


Challenge 5. Docker Compose it
Docker Compose

Once you've got dockerized all the API components (python app and database), you are ready to make a docker-compose file. KISS.
no tengo experiencia en dockers ni dockercompose , pero investigando he podido llegar a dicha solución, en la que
nos permitirá desplegar los 2 contenedores creados anteriormente:
version: '3'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile-app (imagen de docker creada anteriormente)
    ports:
      - 8000:8000 (puerto a exponer la app)
    depends_on:
      - db   (depende de db que es la base de datos mongodb)
  db:
    build:
      context: .
      dockerfile: Dockerfile-mongodb
    ports:
      - 27017:27017   (puerto donde expondremos la bbdd)
    volumes:
      - ./data:/data/db   (volumen donde persistiran los datos de los restaurantes)

Para ejecutarlo: docker-compose up
nota: tener el dockerfile en el mismo directorio de dockercompose

Final Challenge. Deploy it on kubernetes
Kubernetes

If you are a container hero, an excellent devops... We want to see your expertise. Use a kubernetes system to deploy the API. We recommend you to use tools like minikube or microk8s.

Write the deployment file (yaml file) used to deploy your API (python app and mongodb).

No tengo experiencia en kubernetes, el siguiente deployment.yaml lo he hecho basandome en documentación en internet, el despliegue
no me ha funcionado, pero el script resultante es el siguiente:
apiVersion: apps/v1
kind: Deployment (en esta parte desplegaremos la app de python)
metadata:
  name: app-deployment
spec:
  replicas: 3 (haremos 3 replicas para asegurar la disponibilidad y tolerancia a fallos)
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers: (ejecuta el contenedor en el puerto 8000)
        - name: app
          image: python:3.6.8
          ports:
            - containerPort: 8080
		  env:
			- name: MONGO_URI
			- value: mongodb://mongodb:27017/restaurant
---
apiVersion: v1  (en esta parte exponemos el contenedor como servicio para poder acceder por http)
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000  (se expontrá en el puerto 80)
  type: LoadBalancer   (tipo LoadBalancer para que kubernetes dirija el tráfico a la replica con menos carga)
---
apiVersion: apps/v1 (esta parte se encarga de desplegar la bbdd mongodb)
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

Para ejecutar el despliegue:
kubectl apply -f deployment.yaml

Para comprobar el estado de los despliegues usar el comando:
kubectl get deployments

y el estado de los servicios con:
kubectl get services.



