# Profeyelar
**Profeyelar** (a.k.a. **Prof. Eyelar** a.k.a. **Professor Eyelar**) is an end-to-end profiling tool for Python projects/services that makes use of a graphical user interface to simplify the profiling process. It is primarily used to profile requests performed against a web server. The interface contains various settings, which The Professor will use to create a container for your service and begin profiling once the Start button is pressed. Prof. Eyelar will then perform requests for the specified URLs and will shut the container down again once finished. The Professor will handle activation and deactivation of the profiling for you once the program runs.

## User Interface
Prof. Eyelar's interface contains various fields, which affect the profiling or to-be-executed requests.
- In **Request URLs**, you can write any relative request URLs for The Professor to try. Multiple URLs can be separated by a new line. The URLs must be relative–Prof. Eyelar will build the absolute URLs using the project's base URL when the time is right.
- **Encode URL Parameters** is a small helper that you can utilize to encode URL parameters when necessary. You can then copy the encoded values and use them in the request URLs.
- **Repetitions** specifies how many times each request should be executed
- **Headers** can be used to specify any headers that should be passed along with the requests. The headers should be specified without quotes and multiple headers separated with new lines. A colon must be used between a header and its value. If you wish to pass an empty string as a value, then leave the space after the colon empty.
  - Example
    ```
    Accept-Fruit: apple
    Accept-Language:
    Accept-Professor: eyelar
    ```
- Profiling with **tracemalloc** and **cProfile** can be activated with the corresponding checkboxes. These profiling options will create `.tracemalloc` and `.cprofile` files, which you can interpret with corresponding tools.
The last profiling option is self-explanatory and can be used to limit RAM. 

## Requirements
Professor Eyelar has high standards and can only work for your service if specific criteria are met.
- **Tkinter**: Profeyelar's interface is created with Tkinter, which will only work for you if a Python version that has been configured for Tkinter has been installed. In Ubuntu, for example, Tkinter is generally not included in the default Python installation, so you may need to install the `python3-tk` package. You can check if Tkinter is installed by writing `import tkinter` in a Python session. The import should succeed without error.
- **Configuration File**: A configuration file in JSON format must be given when calling Profeyelar from the terminal. This file contains information that The Professor will need in order to be able to create a container for your service and save the profiling results. Refer to [Structure of the Configuration File](#structure-of-the-configuration-file) for info on what this file should look like.
- **Server**: Since Prof. Eyelar is primarily used to profile requests to a web server, your project needs to have a server that The Professor can send requests to once the container has started.
- **Docker**: The Professor uses Docker commands to create containers for services and profile them, so the Docker Engine is required
- **Entrypoint**: Profeyelar requires you to implement a `serve-with-eyelar` entrypoint, in which you prepend the command used to start your server with `$*`. This will insert all the arguments that The Professor passes when calling that entrypoint. These arguments essentially wrap the server start in a call to memray, which will be used to profile while the server is active.

## Structure of the Configuration File
### Fields
- **base_url** (`string`, required): Absolute base URL of your service. The Professor will combine the relative request URLs with this base URL to build the absolute request URLs.
- **name** (`string`, required): The name of your service. The Professor needs it in order to run his commands on the service container he will create.
- **api_docs_url** (`string` or `null`, required): If your project has API-Docs that can be reached via URL, you can insert the absolute URL here. Prof. Eyelar will then include an `Open API Docs` button in its interface, which will open the corresponding page in your browser. This can be helpful if you need to quickly reference the Docs to formulate API-Calls in the relative request URLs correctly
- **output_directory** (`string`, required): Where Professor Eyelar should save the profiling results. Important to note is that this refers to a directory in the **profiled container's filesystem**. Therefore, if you want to access the results, you should ensure the output directory path in question is mapped to a specific path on the host system, which you can access after the container has stopped. Otherwise, you would lose the results after the profiling is complete because The Professor will then shut down the container.
- **retry_count** (`number`, optional, default 30): Specifies how many times The Professor will attempt to reach the built container before giving up and cancelling the profiling session. Changing the value for this setting can make sense for larger projects that may need more time to build and start a container for. Professor Eyelar checks the availability of the service container with a readiness probe, which, if unsuccessful, is repeated as many times as specified by `retry_count`. As soon as one of these probes succeeds, Prof. Eyelar will begin performing the user-specified requests.

### Usage of environment variables in strings
You can reference available environment variables in `string` values of the configuration file. To do so, you simply wrap the variable name in `$ENV{}`. An example of this can be seen in [Example Configuration File](#example-configuration-file).

### Example Configuration File
```json
{
    "service": {
        "base_url": "http://$ENV{PROJECT_NAME}.com/",
        "name": "$ENV{PROJECT_NAME}",
        "api_docs_url": null
    },
    "profiling": {
        "output_directory": "i/am/a/directory/hehe/"
    }
}
```

## Output Files
Profeyelar can generate up to 3 different types of profile result files, which can be analyzed with corresponding tools
- **Memray (`.bin`) Files**: Profiling results for memray will always be generated. These files end in `.bin` and have _memray_ in their name. You will need memray in order to generate reports from the data in these files. For more info about memray and the different generable reports, you can refer to their documentation [here](https://bloomberg.github.io/memray/getting_started.html).
- **Tracemalloc (`.tracemalloc`) Files**: Tracemalloc snapshots will only be generated if the corresponding option is activated in the Profeyelar user interface. These files end in `.tracemalloc`, and results can be viewed with corresponding functions of the [tracemalloc](https://docs.python.org/3/library/tracemalloc.html) module
- **cProfile (`.cprofile`) Files**: cProfile Stats will only be generated if the corresponding option is activated in the Profeyelar user interface. These files end in `.cprofile`, and results can be interpreted with corresponding tools like [pstats](https://docs.python.org/3.15/library/pstats.html) or [snakeviz](https://pypi.org/project/snakeviz/)

## Note regarding Gevent
As of time of writing, running memray on gunicorn based servers with `GeventWorker` workers results in an error when the server is stopped. We discovered this by chance when we checked the container logs before Profeyelar had finished the container shutdown process. The error does not seem to prevent The Professor from saving the profiling results and shutting the container down successfully. However, it is good to be aware of this behavior nonetheless. We did not encounter a similar error when running a gunicorn based server with Gthread (`ThreadWorker` workers) instead.