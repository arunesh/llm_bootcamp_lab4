# LLM Bootcamp Week 4 Lab

## Status:

 Completed Milestone 6.
```
 app.py for milestone 4.
 app_m5.py for milestone 5.
 app_m6.py for milestone 6.
 ```

## Basics


```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Copy the `.env.sample` file to a new file named `.env`
- Fill in the `.env` file with your API keys

```bash
chainlit run app.py -w
``` 

## Updating dependencies

If you need to update the project dependencies, follow these steps:

1. Update the `requirements.in` file with the new package or version.

2. Install `pip-tools` if you haven't already:
   ```bash
   pip install pip-tools
   ```

3. Compile the new `requirements.txt` file:
   ```bash
   pip-compile requirements.in
   ```

4. Install the updated dependencies:
   ```bash
   pip install -r requirements.txt
   ```

