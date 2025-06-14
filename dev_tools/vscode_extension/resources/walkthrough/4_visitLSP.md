# Apache Hamilton Language Server

Apache Hamilton VSCode uses a [Language Server](https://microsoft.github.io/language-server-protocol/) to build a dataflow from your currently active file.

Current features include:
- view the dataflow
- completion suggestions

## Debugging

You can view the server logs to inspect unexpected behaviors or bugs. The log level will match the `VSCode Log Level`. Set it to `Debug` for further details.

> ⚠
> - If the visualization doesn't update or is slow, close and reopen the activity bar (`ctrl+b`) or the panel (`ctrl+j`)
> - If you encountered freezes, open the command palette `ctrl+p` and use `Developer: Reload Window`.
