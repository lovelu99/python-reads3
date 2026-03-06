pipeline {
    agent any
    environment {
        IMAGE_NAME = "reads3"
        DOCKERHUB_REPO = "noakhali/reads3"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Build'){
            steps {
                 echo 'building and tagging for dockerhub..'
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
                sh 'docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERHUB_REPO}:${IMAGE_TAG}'

            }
        }
        stage('push to dockerhub'){
            steps {
              
              echo 'pushing to dockerhub..'

                    withCredentials([usernamePassword(credentialsId: 'dockerhub', passwordVariable: 'password', usernameVariable: 'uname')]) {
                    sh 'docker login -u $uname -p $password'
                    sh 'docker push ${DOCKERHUB_REPO}:${IMAGE_TAG}'
                    sh 'docker logout'
                    }
            }
        }
        stage ('Clean Images') {
            steps {
                echo 'Cleaning up local images...'
                sh 'docker rmi ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKERHUB_REPO}:${IMAGE_TAG} || true'
            }
        }
        stage('Trigger Kubernetes Deployment') {
            steps {
                echo 'Updating argo cd repository...'
                build job: 'deployment', parameters: [string(name: 'IMAGE_TAG', value: "${IMAGE_TAG}")]
            }
        }
        stage('Clean workspace') {
            steps {
                echo 'Cleaning up workspace...'
                cleanWs()
            }
        }
    }
}