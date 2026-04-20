## To Run:

### Activate Virtual Environment



```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt  # Install dependencies
```


### Create .env file

``` bash
echo "GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" > .env
```

### Run scripts in this order:

1. **On person runs and then shares `data/repos.json` with the other**:
```bash
python collect_repos.py
```


2. Each person runs their own:

``` bash
# Evan's machine:
python collect_issues.py --researcher evan

# and then (after colect_issues) 

python collect_commits.py --researcher evan


# Stefan's machine:
python collect_issues.py --researcher stefan

# then

python collect_commits.py --researcher stefan

```

3. Share files and merge into one dataset using `merge_shards.py`

