## How to publish to Pypi

```bash
python3 -m build
python3 -m twine upload --repository testpypi dist/* # change testpypi to pypi for actual release
```