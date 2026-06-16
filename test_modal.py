import modal

app = modal.App("test")

@app.function()
def hello():
    return "Modal is working 🚀"
