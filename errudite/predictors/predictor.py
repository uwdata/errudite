from typing import List, Dict, Any
from ..utils import Registrable

class Predictor(Registrable):
    """A base class for predictors.
    A predictor runs prediction on raw texts and also instances.
    It also saves the performance score for the predictor.
        
    This is a subclass of ``errudite.utils.registrable.Registrable`` and all the actual rewrite 
    rule classes are registered under ``Predictor`` by their names.

    Parameters
    ----------
    name : str
        The name of the predictor.
    description : str
        A sentence describing the predictor.
    model : any
        The executable model.
    perform_metrics : List[str]
        The name of performance metrics.
    
    Attributes
    ----------
    perform : Dict[str, float]
        .. code-block:: js
            
            { perform_name: the averaged performance score. }
    """
    def __init__(self, 
        name: str, 
        description: str, 
        model: any,
        perform_metrics: List[str]):
        self.name: str = name
        self.description: str = description
        self.predictor: Any = model
        self.perform: Dict[str, float] = {}
        self.perform_metrics: List[str] = perform_metrics

        for p in self.perform_metrics:
            self.perform[p] = 0
    
    def predict(self, **kwargs):
        """
        run the prediction.

        Raises
        ------
        NotImplementedError
           Should be implemented in subclasses.
        """
        raise NotImplementedError

    def evaluate_performance(self, instances: List['Instance']) -> None:
        """Save the performance of the predictor.
        It iterates through metric names in ``self.perform_metrics``, and average the 
        corresponding metrics in ``instance.prediction.perform``. It saves the results
        in ``self.perform``.
        
        Parameters
        ----------
        instances : List[Instance]
            The list of instances, with predictions from this model already saved as
            part of its entries.
        
        Returns
        -------
        None
            The result is saved in ``self.perform``.
        """
        instances = list(filter(lambda i: i.vid==0, instances))
        n_total = len(instances)
        if n_total != 0:
            for metric in self.perform_metrics:
                self.perform[metric] = sum([
                    i.get_entry('prediction', self.name).perform[metric] for i in instances]) / n_total
        else:
            print(n_total)
            print(self.name)
    
    def serialize(self) -> Dict:
        """Seralize the instance into a json format, for sending over
        to the frontend.
        
        Returns
        -------
        Dict[str, Any]
            The serialized version.
        """
        return {
            'perform': self.perform,
            'name': self.name,
            'description': self.description
        }
    
    def __repr__(self) -> str:
        """
        Override the print func by displaying the class name and the predictor name.
        """
        return f'{self.__class__.__name__} {self.name}'
    
    @classmethod
    def create_from_json(cls, raw: Dict[str, str]) -> 'Predictor':
        """
        Recreate the predictor from its seralized raw json.
        
        Parameters
        ----------
        raw : Dict[str, str]
            The json version definition of the predictor, with 
            name, description, model_path, and model_online_path.

        Returns
        -------
        Predictor
            The re-created predictor.
        """
        try:
            return Predictor.by_name(raw["model_class"])(
                name=raw["name"], 
                description=raw["description"],
                model_path=raw["model_path"],
                model_online_path=raw["model_online_path"])
        except:
            raise
    
    @classmethod
    def model_predict(cls, 
        predictor: 'Predictor', 
        **targets) -> 'Label':
        """
        Define a class method that takes Target inputs, run model predictions, 
        and wrap the output prediction into Labels.
        
        Parameters
        ----------
        predictor : Predictor
            A predictor object, with the predict method implemented.
        targets : Target
            Targets in kwargs format

        Returns
        -------
        Label
            The predicted output, with performance saved.
        
        Raises
        -------
        NotImplementedError
            This needs to be implemented per task.
        """
        raise NotImplementedError