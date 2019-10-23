# Hyper Model

Hyper Model helps take Machine Learning to production.

Hyper Model takes an opinionated and simple approach to the deployment, testing and monitoring of Machine Learning models, leveraging Kubernetes and Kubeflow to do all the important work.

# Getting started

## 1. Install conda

## 2. Create a conda environment

```
conda create --name hypermodel python=3.7
conda activate hypermodel
```

## 3. Install the HyperModel pip package for local development

```
cd src/hyper-model/
python -m pip install --upgrade setuptools wheel
python setup.py sdist bdist_wheel
pip install -e .
```

# Example Pipeline

```
config = {
  "lake_path": "./lake",
  "warehouse_path": "./warehouse/sqlite-warehouse.db"
}

app = PipelineApp(name="crashed_model", platform="local", config-config)

@app.pipeline()
def my_pipeline(name):

  a = step_a(name)
  b = step_b(name)

  # Execute b after a
  b.after(a)

@app.pipeline.op():
def step_a(firstname):
  print(f"hello {firstname}")


@app.pipeline.op():
def step_b(firstname):
  print(f"goodbye {firstname}")


```

# Anatomy of an ML Project in Hyper Model

<<<<<<< HEAD
Hyper Model Projects provide are self-contained Python Packages, providing all the code required for both Training and Prediction phase. Hyper Model Projects are executable locally as console scripts.
=======
Hyper Model Projects provide are self-contained Python Packages, providing all the code required for both Training and Inferences phases. Hyper Model Projects are executable locally as console scripts.
>>>>>>> origin/master

Project layout:

- demo_pkg/
<<<<<<< HEAD
  - training
    - extract_data.py
      def extract_training()
      def extract_test()
    - features.py
      def encode()
      def normalize()
    - training.py
      def train_model()
      def evaluate_model()
    - pipeline.py
      def my_pipeline()
  - prediction
    - prediction.py
      def start_dev()
      def start_prod()
      def batch_predict(csv_path)

Under this layout, you can invoke the feature.encode() function with the following command:

```
demo training feature encode
```

Similarly, to do a batch prediction, you could invoke the tool with:

```
demo prediction batch-predict --csv-path=./unlabeled.csv
```

To make this majesty real, all you need to do is to define your pipeline entrypoint with:

`my_pipeline.py`

```
from .extract_data import extract_training, extract_test
from .features import encode, normalize
from .training import train_model, evaluate_model

@hm.pipeline()
def my_pipeline():
    op_extract_training = extract_training().op
    op_extract_test = extract_test().op.after(op_extract_training)

    op_encode = encode().op.after(op_extract_test)
    op_normalize = normalize().op.after(op_extract_test)

    op_train_model = train_model().op.after(op_encode)
    op_evaluate_model = evaluate_model().op.after(op_train_model)


```

`features.py`

```
from .pipeline import my_pipeline

@hm.op(pipeline=my_pipeline)
def encode(context):
    pass
```

This would then allow you to execute your entire pipeline locally with the following command:

```
demo my-pipeline all
```

Or you can execute a single step with:

```
demo my-pipeline features encode
```

# Deployment of ML Pipelines to Kubeflow

```

```
=======
  - demo
    - pipeline.py
    - inference.py
    - shared.py
    - app.Dockerfile
    - inference_deployment.yml
    - start.py
  - setup.py
  - Readme.md

Lets run through the purpose of each file:

## setup.py

This file is reponsible for defining the Python Package that this application will be run as, as per
any other python package.

## start.py

This is our entrypoint into the application (HmlApp), along with its two central components the HmlPipelineApp
(used for data processing and training) and the HmlInferenceApp (used for generating inferences / predictions
via Json API).

### Code Walkthrough

#### Set up config

```
    config = {
        "package_name": "crashed",
        "script_name": "crashed",
        "container_url": "growingdata/demo-crashed:tez-test",
        "port": 8000
    }
```

This sets up shared configuration used by the application. The `container_url` is the docker based url
to the current version of the container. The container should be build during ci/cd - although it may also
be build locally, using the following commands:

```
docker build -t growingdata/demo-crashed:tez-test -f ./demo/car-crashes/crashed.Dockerfile .
docker push growingdata/demo-crashed:tez-test
```

Where you will need to update the url's to something that you have permission to write to.

#### Define the application context object

```
    app = hml.HmlApp(name="model_app", platform="GCP", config=config)
```

An HmlApp is responsible for managing both the Pipeline and Inference phases of the application, helping
to manage shared functionality, such as the CLI.

#### Define & Register a reference for the ML Model

```
    crashed_model = shared.crashed_model_container(app)
    app.register_model(shared.MODEL_NAME, crashed_model)
```

HyperModel maintains a reference to the current Model, which is generated at the end of the Pipeline
execution and then loaded on Initialization of the Inference Application. This reference contains
information such as how features can be encoded, normalisation parameters and a reference to the actual
joblib file encoding the model.

#### Define your Pipeline

```
    @hml.pipeline(app.pipelines, cron="0 0 * * *", experiment="demos")
    def crashed_pipeline():
        """
        This is where we define the workflow for this pipeline purely
        with method invocations.
        """
        create_training_op = pipeline.create_training()
        create_test_op = pipeline.create_test()
        train_model_op = pipeline.train_model()

        # Set up the dependencies for this model
        (
            train_model_op
            .after(create_training_op)
            .after(create_test_op)
        )
```

This method defines the Kubeflow Pipeline `crashed_pipeline` which will be deployed using the `demos`
experiment within Kubeflow. Each function invocation within the `crashed_pipeline()` method defines
Kubeflow ContainerOps which execute the `script_name` defined above in `config` with the correct CLI
parameters.

The `@hml.pipeline` decorator is essentially a wrapper for the Kubeflow SDK's `@dsl.pipeline` decorator
but with additional functionality to enable each `ContainerOp` to be executed via the command line.

#### Configure the execution context of the container

```
    @hml.configure_op(app.pipelines)
    def op_configurator(op):
        """
        Configure our Pipeline Operation Pods with the right secrets and
        environment variables so that it can work with our cloud
        provider's services
        """
        (op
            # Service account for authentication / authorisation
            .with_gcp_auth("svcacc-tez-kf")
            .with_env("GCP_PROJECT", "grwdt-dev")
            .with_env("GCP_ZONE", "australia-southeast1-a")
            .with_env("K8S_NAMESPACE", "kubeflow")
            .with_env("K8S_CLUSTER", "kf-crashed")
        )
        return op
```

Containers require configuration, which is done by using the `@hml.configure_op(app.pipelines)` decorator
on a method accepting an `hml.HmlContainerOp` as its parameter. This function enables us to manipulate the
final container definition within the Kubeflow Pipelines Workflow so that we can bind secrets, bind environment
variables, mount volumes, etc.

#### Configure your Inference API

```
    @hml.inference(app.inference)
    def crashed_inference(inference_app: hml.HmlInferenceApp):
        # Get a reference to the current version of my model
        model_container = inference_app.get_model(shared.MODEL_NAME)
        model_container.load()

        # Define our routes here, which can then call other functions with more
        # context
        @inference_app.flask.route("/predict", methods=["GET"])
        def predict():
            logging.info("api: /predict")

            feature_params = request.args.to_dict()
            return inference.predict_alcohol(inference_app, model_container, feature_params)

```

When the inference application is executed (e.g. with `crashed inference run-dev`), this function will be
executed prior to the Flask application starting. This provides us with an opportunity to load the required
model into memory (e.g. from the DataLake) using `model_container.load()`.

With the model loaded into memory, we can also define our routes to actually make predictions. In this example
we are simple passing the execution context to the method defined in `inference.predict_alcohol()`.

## pipeline.py

This module defines our different pipeline operations, with functions decorated with `@hml.op()` representing
Kubeflow Operations to be run within a Pipeline. Importantly, Kubeflow Operations are designed to be re-used
and thus are only bound to a Pipeline at run time, via the function decorated with @hml.pipeline().

It is importand that the pipeline build a "ModelContainer" object, serialized as JSON which contains details about the newly trained model, including a reference to the joblib file defining the final model. This `ModelContainer` object will be loaded by the `InferencesApp`

## shared.py

Both the Training and Inference phases of the project will share functionality, especially regarding key elements of pre-processing such as encoding & normalisation. Methods relating to shared functionality live in this file by way of example, but obviously may span multiple modules.

## inference.py

This module provides functionality to create inferences based on data, without all fuss of dealing with Flask, HyperModel or other libraries.

# Command Line Interface

All Hyper Model applications can be run from the command line using intuitive commands:

## Execute a Pipeline Step

```
<your_app> pipelines <your_pipeline_name> run <your_pipeline_step>
```

## Run all steps in a Pipeline

```
<your_app> pipelines <your_pipeline_name> run-all
```

## Deploy your Pipeline to Kubeflow (Development)

```
<your_app> pipelines <your_pipeline_name> deploy-dev
```

## Deploy your Pipeline to Kubeflow (Production)

```
<your_app> pipelines <your_pipeline_name> deploy-prod
```

## Serve Inference Requests (dev)

Run using the Flask based development environment

```
<your_app> inference run-dev
```

## Serve Inference Requests (prod)

Run using the Waitress based serving engine

```
<your_app> inference run-prod
```
>>>>>>> origin/master

# Development setup

```
conda create --name hml-dev python=3.7
activate hml-dev
<<<<<<< HEAD
cd src\hyper-model\
pip install -e ,

=======
conda install -n hml-dev mypy pandas joblib flask waitress click tqdm


cd src\hyper-model\
pip install -e ,
>>>>>>> origin/master
pip install mypy

```

Set Visual Studio Code to use the newly created `hml-dev` environment
