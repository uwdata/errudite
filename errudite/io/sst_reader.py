from typing import Dict, List

from overrides import overrides
from nltk.tree import Tree

from .dataset_reader import DatasetReader
from ..utils import ConfigurationError, normalize_file_path
from ..targets.instance import Instance
from ..targets.target import Target
from ..targets.label import PredefinedLabel
import logging
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name

@DatasetReader.register("sst")
class SSTReader(DatasetReader):
    """
    This loads the data from The Stanford Sentiment Treebank (SNLI) Corpus:
    https://nlp.stanford.edu/sentiment/treebank.html

    * default evaluation metric: accuracy
    * target entries in an instance: query, predictions, groundtruth.


    This can be queried via:
    
    .. code-block:: python

        from errudite.io import DatasetReader
        DatasetReader.by_name("sst")
    """
    def __init__(self, cache_folder_path: str=None, use_subtrees: bool = False,
                 granularity: str = "5-class") -> None:
        super().__init__(cache_folder_path)
        self._use_subtrees = use_subtrees
        allowed_granularities = ["5-class", "3-class", "2-class"]
        if granularity not in allowed_granularities:
            raise ConfigurationError("granularity is {}, but expected one of: {}".format(
                    granularity, allowed_granularities))
        self._granularity = granularity

    @overrides
    def _read(self, file_path: str, lazy: bool, sample_size: int):
        SEP = "@@:UNK:@@"
        def add_indices_to_terminals(treestring):
            tree = Tree.fromstring(treestring)
            for idx, _ in enumerate(tree.leaves()):
                tree_location = tree.leaf_treeposition(idx)
                non_terminal = tree[tree_location[:-1]]
                non_terminal[0] = non_terminal[0] + SEP + str(idx)
            return str(tree)

        with open(normalize_file_path(file_path), "r") as data_file:
            logger.info("Reading instances from lines in file at: %s", file_path)
            for idx, line in enumerate(data_file.readlines()):
                line = line.strip("\n")
                if not line:
                    continue
                if lazy:
                    parsed_line = Tree.fromstring(line)
                    yield parsed_line.leaves()
                    if sample_size and idx > sample_size:
                        break
                    continue
                line = add_indices_to_terminals(line)
                parsed_line = Tree.fromstring(line)
                if self._use_subtrees:
                    for _, subtree in enumerate(parsed_line.subtrees()):
                        strs = subtree.leaves()
                        token_idxes = [ t.split(SEP) for t in strs ]
                        tokens = [ t[0] for t in token_idxes ]
                        idxes = [ int(t[1]) for t in token_idxes ]
                        subtree_idxes = (min(idxes), max(idxes)+1)
                        instance = self._text_to_instance(
                            f'q:{idx}:t[{subtree_idxes[0]}, {subtree_idxes[1]}]', 
                            tokens, 
                            subtree.label(), 
                            metas={ "subtree_idxes": subtree_idxes })
                        if instance is not None:
                            yield instance
                else:
                    strs_ = parsed_line.leaves()
                    metas = {
                        "nsubtree": len(list(parsed_line.subtrees())),
                        "subtree_idxes": []
                    }
                    for _, subtree in enumerate(parsed_line.subtrees()):
                        strs = subtree.leaves()
                        token_idxes = [ t.split(SEP) for t in strs ]
                        tokens = [ t[0] for t in token_idxes ]
                        idxes = [ int(t[1]) for t in token_idxes ]
                        subtree_idxes = [min(idxes), max(idxes)+1]
                        metas["subtree_idxes"].append({
                            "idx": (subtree_idxes[0], subtree_idxes[1]),
                            "label": self._normalize_sentiment(subtree.label())
                        })
                    instance = self._text_to_instance(
                        f'q:{idx}', 
                        [ t.split(SEP)[0] for t in strs_ ], 
                        parsed_line.label(),
                        metas=metas)
                    if instance is not None:
                        yield instance
                if sample_size and idx > sample_size:
                    break
    
    @overrides
    def _text_to_instance(self, id: str, tokens: List[str], sentiment: str = None, metas: Dict={}) -> Instance:  # type: ignore
        query = Target(qid=str(id), text=' '.join(tokens), vid=0, metas=metas)
        instance = Instance(qid=str(id), vid=0)
        sentiment = self._normalize_sentiment(sentiment)
        if sentiment is not None:
            groundtruth = PredefinedLabel(
                model='groundtruth', 
                qid=str(id), vid=0,
                text=sentiment
            )
            instance.set_entries(query=query, groundtruth=groundtruth)
            return instance
        return None
    
    def _normalize_sentiment(self, sentiment: str):
        # 0 and 1 are negative sentiment, 2 is neutral, and 3 and 4 are positive sentiment
        # In 5-class, we use labels as is.
        # 3-class reduces the granularity, and only asks the model to predict
        # negative, neutral, or positive.
        # 2-class further reduces the granularity by only asking the model to
        # predict whether an instance is negative or positive.
        if not sentiment:
            return None
        if self._granularity == "3-class":
            if int(sentiment) < 2:
                sentiment = "0"
            elif int(sentiment) == 2:
                sentiment = "1"
            else:
                sentiment = "2"
        elif self._granularity == "2-class":
            if int(sentiment) < 2:
                sentiment = "0"
            elif int(sentiment) == 2:
                return None
            else:
                sentiment = "1"
        return sentiment