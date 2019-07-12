# Errudite

**This opensourcing is work-in-progress!**

Errudite is an interactive tool for scalable, reproducible, and counterfactual error analysis. 
Errudite provides an expressive domain-specific language for extracting relevant features of
linguistic data, which allows users to visualize data attributes, group relevant instances,
and perform counterfactual analysis across all available validation data. 


## Getting Started

1. Watch [this video demo](https://youtu.be/Dil5i0AYyu8) that contains the highlights of Errudite's functions & use cases 
2. Get [set up](#installation) quickly
3. Try [Errudite's user interface](#gui-server) on machine comprehension
4. Try the [tutorials on JupyterLab notebooks](#jupyterLab-tutorial)
5. Read the [documentation](https://errudite.readthedocs.io/en/latest/)

## Citation
If you are interested in this work, please see our 
[ACL 2019 research paper](https://homes.cs.washington.edu/~wtshuang/files/acl2019_errudite.pdf)
and consider citing our work:
```
@inproceedings{2019-errudite,
    title = {Errudite: Scalable, Reproducible, and Testable Error Analysis},
    author = {Wu, Tongshuang and Ribeiro, Marco Tulio and Heer, Jeffrey and Weld Daniel S.},
  booktitle={the 57th Annual Meeting of the Association for Computational Linguistics (ACL 2019)},
    year = {2019},
    url = {https://homes.cs.washington.edu/~wtshuang/files/acl2019_errudite.pdf},
}
```

## Quick Start

### Installation

#### PIP
Errudite requires Python 3.6.x. The package is avaiable through `pip`: 
Just install it in your Python environment and you're good to go!

```SH
# create the virtual environment
virtualenv --no-site-packages -p python3.6 venv
# activate venv
source venv/bin/activate
# install errudite
pip install errudite
```

#### Install from source

You can also install Errudite by cloning our git repository:

```sh
git clone https://github.com/uwdata/errudite
```

Create a Python 3.6 virtual environment, and install Errudite in `editable` mode by running:

```sh
pip install --editable .
```

This will make `errudite` available on your system but it will use the sources from the local clone
you made of the source repository.

#### 
1. `mysql_config not found` for `Pattern`: See similar solutions [here](https://github.com/PyMySQL/mysqlclient-python#prerequisites).


### GUI Server

Errudite has a UI wrapped for Machine Comprehension and Visual Question Answering tasks.
The interface integrates all the key analysis functions (e.g., inspecting instance attributes,
grouping similar instances, rewriting instances), It also provides exploration 
support such as visualizing data distributions, suggesting potential queries, and presenting the 
grouping and rewriting results. While not strictly necessary, it makes their application much 
more straightforward.

To get a taste of GUI for the machine comprehension task, you should first download a cache folder 
for preprocessed [SQuAD](https://rajpurkar.github.io/SQuAD-explorer/) instances, which will help you
skip the process of running your own preprocessing:

```
python -m errudite.download

Commands:
    cache_folder_name
                A folder name. Currently, we allow downloading the following:
                squad-100, squad-10570.
    cache_path  A local path where you want to save the cache folder to.
```

Then, we need to start the server: 

```sh
# the model relies on Allennlp, so make sure you install that first.
pip install allennlp==0.8.4
source venv/bin/activate
python -m errudite.server

Commands:
    config_file
                A yaml config file path.
```
The config file looks like the following (or in [config.yml](config.yml)):

```yml
task: qa # the task, should be "qa" and "vqa".
cache_path: {cache_path}/{cache_folder_name}/ # the cached folder.
model_metas: # a model.
- name: bidaf
  model_class: bidaf # an implemented model class
  model_path: # a local model file path
  # an online path to an Allennlp model
  model_online_path: https://s3-us-west-2.amazonaws.com/allennlp/models/bidaf-model-2017.09.15-charpad.tar.gz
  description: Pretrained model from Allennlp, for the BiDAF model (QA)
attr_file_name: null # It set, to load previously saved analysis.
group_file_name: null
rewrite_file_name: null
```

Then visit `http://localhost:5000/` in your web browser.


### JupyterLab Tutorial

Besides used in a GUI, errudite also serves as a general python package. The tutorial goes
through:
1. Preprocessing the data, and extending Errudite to different tasks & predictors
2. Creating data attributes and data groups with a domain specific language (or your customized functions).
3. Creating rewrite rules with the domain specific language (or your customized functions).

To go through the tutorial, do the following steps:

```sh
# clone the repo
git clone https://github.com/uwdata/errudite
# initial folder: errudite/
# create the virtual environment
virtualenv --no-site-packages -p python3.6 venv
# activate venv
source venv/bin/activate

# run the default setup script
pip install --editable .

# get to the tutorial folder, and start!
cd tutorials
pip install -r requirements_tutorial.txt
jupyter lab
```
