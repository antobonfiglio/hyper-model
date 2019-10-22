import logging
import click
from typing import Dict, List
from hypermodel import hml

from titanic.tragic_titanic_shared import titanic_model_container, build_feature_matrix
from titanic.tragic_titanic_pipeline import create_training, create_test, train_model


def main():
    config = {
        "package_name": "titanic",
        "script_name": "titanic",
        "container_url": "growingdata/demo-tragic_titanic",
        "port": 8000
    }

    # Create a reference here so that we can
    app = hml.HmlApp(name="local_model_app", platform="Local", config=config)

    def op_configurator(op):
        """
        Configure our Pipelines Pods with the right secrets and 
        environment variables so that it can work with the cloud
        providers services
        """
        # (op
        #     # Service account for authentication / authorisation
        #     .with_gcp_auth("svcacc-tez-kf")  
        #     .with_env("GCP_PROJECT", "grwdt-dev")   
        #     .with_env("GCP_ZONE", "australia-southeast1-a")   
        #     .with_env("K8S_NAMESPACE", "kubeflow") 
        #     .with_env("K8S_CLUSTER", "kf-crashed") 
        #     # Data Lake Config
        #     .with_env("LAKE_BUCKET", "grwdt-dev-lake") 
        #     .with_env("LAKE_PATH", "crashed") 
        #     # Data Warehouse Config
        #     .with_env("WAREHOUSE_DATASET", "crashed") 
        #     .with_env("WAREHOUSE_LOCATION", "australia-southeast1") 
        #     # Track where we are going to write our artifacts
        #     .with_empty_dir("artifacts", "/artifacts")
        #     .with_env("KFP_ARTIFACT_PATH", "/artifacts") 
        # )
        return op

    @hml.pipeline(app=app, cron="0 0 * * *", experiment="demos")
    def tragic_titanic_pipeline():
        """
        This is where we define the workflow for this pipeline purely
        with method invocations, because its super cool!
        """
        create_training_op = create_training()
        create_test_op = create_test()
        train_model_op = train_model()

        # Set up the dependencies for this model
        (
            train_model_op
            .after(create_training_op)
            .after(create_test_op)
        )

    titanic_model = titanic_model_container(app)

    app.register_model(titanic_model)
    app.pipelines.configure_op(op_configurator)
    app.start()


# main()
