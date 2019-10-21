import click
import json
from datetime import datetime
from kfp import dsl
from kfp import Client
from kfp.compiler import Compiler
from typing import List, Dict, Callable
from hypermodel.hml.hml_container_op import HmlContainerOp, _pipeline_enter, _pipeline_exit
from hypermodel.kubeflow.kubeflow_client import KubeflowClient
from hypermodel.kubeflow.deploy import deploy_pipeline


class HmlPipeline:
    def __init__(self, config: Dict[str, str], cli, pipeline_func, op_builders):
        self.config = config
        self.name = pipeline_func.__name__
        self.pipeline_func = pipeline_func
        self.kubeflow_pipeline = dsl.pipeline(pipeline_func, pipeline_func.__name__)

        self.cron = None
        self.experiment = None

        # The methods we use to configure our Ops for running in Kubeflow
        self.op_builders = op_builders

        self.ops_list = []
        self.ops_dict = {}

        # We treat the pipeline as a "group" of commands, rather than actually executing
        # anything.  We can then bind a
        self.cli_pipeline = click.group(name=pipeline_func.__name__)(_pass)

        # Register this with the root `pipeline` command
        cli.add_command(self.cli_pipeline)

        # Create a command to execute the whole pipeline
        self.cli_all = click.command(name="run-all")(self.run_all)

        self.deploy_dev = self.apply_deploy_options(click.command(name="deploy-dev")(self.deploy_dev))
        self.deploy_prod = self.apply_deploy_options(click.command(name="deploy-prod")(self.deploy_prod))

        self.cli_pipeline.add_command(self.cli_all)
        self.cli_pipeline.add_command(self.deploy_dev)
        self.cli_pipeline.add_command(self.deploy_prod)

        self.workflow = self._get_workflow()
        self.dag = self.get_dag()
        self.tasks = self.dag["tasks"]
        self.task_map = dict()

        for t in self.tasks:
            task_name = t["name"]
            self.task_map[task_name] = t

    def apply_deploy_options(self, func):
        func = click.option("-h", "--host", required=False, help="Endpoint of the KFP API service to connect.")(func)
        func = click.option("-c", "--client-id", required=False, help="Client ID for IAP protected endpoint.")(func)
        func = click.option("-n", "--namespace", required=False, default="kubeflow", help="Kubernetes namespace to connect to the KFP API.")(func)
        return func

    def with_cron(self, cron):
        self.cron = cron
        return self

    def with_experiment(self, experiment):
        self.experiment = experiment
        return self

    def deploy_dev(self, host: str = None, client_id: str = None, namespace: str = None):
        deploy_pipeline(self, "dev", host, client_id, namespace)

    def deploy_prod(self, host: str = None, client_id: str = None, namespace: str = None):
        deploy_pipeline(self, "prod", host, client_id, namespace)

    def run_all(self, **kwargs):
        run_log = dict()

        for t in self.tasks:
            task_name = t["name"]
            self.run_task(task_name, run_log, kwargs)

    def run_task(self, task_name, run_log, kwargs):
        if task_name not in self.task_map:
            raise Exception(f"Unable to run task: {task_name}, not found in Workflow for pipeine: {self.name}")

        if task_name not in self.ops_dict:
            raise Exception(f"Unable to run task: {task_name}, not found in Ops for pipeine: {self.name}")

        # Check to make sure we havent' already run
        if task_name in run_log:
            return

        task = self.task_map[task_name]
        hml_op = self.ops_dict[task_name]

        # Run my dependencies recusively
        if "dependencies" in task:
            for d in task["dependencies"]:
                if d not in run_log:
                    self.run_task(d, run_log, kwargs)

        # Run the actual one
        ret = hml_op.invoke(**kwargs)
        run_log[hml_op.k8s_name] = True

    def get_dag(self):
        templates = self.workflow["spec"]["templates"]
        for t in templates:
            if "dag" in t:
                return t["dag"]
        return None

    def _add_op(self, hmlop):
        self.ops_list.append(hmlop)

        self.ops_dict[hmlop.k8s_name] = hmlop

        for f in self.op_builders:
            f(hmlop)

        # Register the op as a command within our pipeline command
        self.cli_pipeline.add_command(hmlop.cli_command)

    def __getitem__(self, key: str):
        """
        Get a reference to a `ContainerOp` added to this pipeline
        via a call to `self.add_op`
        """
        return self.ops_dict[key]

    def _get_workflow(self):
        """
        The Workflow dictates how the pipeline will be executed
        """

        # Go and compile the workflow, which will mean executing our
        # pipeline function.  We store a global reference to this pipeline
        # while we are compiling to allow us to easily bind the pipeline
        # to the `HmlContainerOp`, without damaging the re-usabulity of the
        # op.
        _pipeline_enter(self)
        workflow = Compiler()._compile(self.pipeline_func)
        _pipeline_exit()

        return workflow


def _pass():
    pass
