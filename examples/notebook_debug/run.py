if __name__ == "__main__":
    import example_error
    from notebook_debugger_plugin import NotebookErrorDebugger

    from hamilton import driver

    dr = driver.Builder().with_modules(example_error).with_adapters(NotebookErrorDebugger()).build()
    dr.execute(["error_function"], inputs={"input": 4})
