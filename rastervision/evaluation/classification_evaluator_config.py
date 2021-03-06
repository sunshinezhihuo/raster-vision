import os
from copy import deepcopy

import rastervision as rv
from rastervision.core import ClassMap
from rastervision.evaluation \
    import (EvaluatorConfig, EvaluatorConfigBuilder)
from rastervision.protos.evaluator_pb2 import EvaluatorConfig as EvaluatorConfigMsg


class ClassificationEvaluatorConfig(EvaluatorConfig):
    """Abstract class for usage with simple evaluators that
    are classification-based.
    """

    def __init__(self,
                 evaluator_type,
                 class_map,
                 output_uri=None,
                 vector_output_uri=None):
        super().__init__(evaluator_type)
        self.class_map = class_map
        self.output_uri = output_uri
        self.vector_output_uri = vector_output_uri

    def to_proto(self):
        sub_msg = EvaluatorConfigMsg.ClassificationEvaluatorConfig(
            class_items=self.class_map.to_proto(),
            output_uri=self.output_uri,
            vector_output_uri=self.vector_output_uri)
        msg = EvaluatorConfigMsg(
            evaluator_type=self.evaluator_type, classification_config=sub_msg)

        return msg

    def update_for_command(self, command_type, experiment_config,
                           context=None):
        if command_type == rv.EVAL:
            if not self.output_uri:
                self.output_uri = os.path.join(experiment_config.eval_uri,
                                               'eval.json')
            if not self.vector_output_uri:
                self.vector_output_uri = os.path.join(
                    experiment_config.eval_uri, 'vector-eval.json')

    def report_io(self, command_type, io_def):
        if command_type == rv.EVAL:
            io_def.add_output(self.output_uri)
            io_def.add_output(self.vector_output_uri)

        return io_def


class ClassificationEvaluatorConfigBuilder(EvaluatorConfigBuilder):
    def __init__(self, cls, prev=None):
        self.config = {}
        if prev:
            self.config = {
                'output_uri': prev.output_uri,
                'vector_output_uri': prev.vector_output_uri,
                'class_map': prev.class_map
            }
        super().__init__(cls, self.config)

    def validate(self):
        if self.config.get('class_map') is None:
            raise rv.ConfigError(
                'class_map not set for ClassificationEvaluatorConfig. '
                'Use "with_class_map".')
        if not isinstance(self.config.get('class_map'), ClassMap):
            raise rv.ConfigError(
                'class_map set with "with_class_map" must be of type ClassMap, got {}'.
                format(type(self.config.get('class_map'))))

    @classmethod
    def from_proto(cls, msg):
        b = cls()
        return b.with_output_uri(msg.classification_config.output_uri) \
                .with_vector_output_uri(msg.classification_config.vector_output_uri) \
                .with_class_map(list(msg.classification_config.class_items))

    def with_output_uri(self, output_uri):
        """Set the output_uri.

            Args:
                output_uri: URI to the stats json to use
        """
        b = deepcopy(self)
        b.config['output_uri'] = output_uri
        return b

    def with_vector_output_uri(self, vector_output_uri):
        """Set the vector_output_uri.

            Args:
                vector_output_uri: URI to the vector stats json to use
        """
        b = deepcopy(self)
        b.config['vector_output_uri'] = vector_output_uri
        return b

    def with_task(self, task):
        """Sets a specific task type, e.g. rv.OBJECT_DETECTION."""
        if not hasattr(task, 'class_map'):
            raise rv.ConfigError('This evaluator requires a task '
                                 'that has a class_map property')
        return self.with_class_map(task.class_map)

    def with_class_map(self, class_map):
        """Set the class map to be used for evaluation.

            Args:
                class_map: The class map to be used

        """
        b = deepcopy(self)
        b.config['class_map'] = ClassMap.construct_from(class_map)
        return b
