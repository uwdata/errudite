from overrides import overrides

from allennlp.common.util import JsonDict
from allennlp.predictors.predictor import Predictor as AllenPredictor

@AllenPredictor.register('mrqa_predictor')
class MRQAPredictor(AllenPredictor):
    def predict_json(self, json_dict: JsonDict) -> JsonDict:
        self._dataset_reader._is_training = False
        if 'header' in json_dict:
            return {}

        predictions = []
        for question_chunks in self._dataset_reader.make_chunks(json_dict, {'dataset':''}):
            question_instances = []
            for instance in self._dataset_reader.gen_question_instances(question_chunks):
                question_instances.append(instance)
            predictions.append(self.predict_batch_instance(question_instances)[0])
        formated_predictions = {pred['qid']:pred for pred in predictions}
        return formated_predictions
