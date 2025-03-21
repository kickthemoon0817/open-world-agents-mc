## Install from repository

1. **Install package managers, uv and conda**:
    - Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/). If you do prefer quick start, you may run `pip install uv` after you created virtual environment.
    - Follow the [miniforge installation guide](https://github.com/conda-forge/miniforge?tab=readme-ov-file#install) to install `conda` and `mamba`. `mamba` is just a faster `conda`. If you've already installed `conda`, you may skip and go ahead. You may use `conda` instead of `mamba`. Installing `conda`/`mamba` is mandatory to utilize `owa-env-gst` EnvPlugin.

2. **Setup virtual environments**:
    - (Recommended) Create new environment with dependencies. `gstreamer` related conda packages are installed.
    ```sh
    mamba env create -n owa -f projects/owa-env-gst/environment_detail.yml
    conda activate owa
    ```
    - If you want to install conda packages in existing environment, run following:
    ```sh
    mamba env update --name (your-env-name-here) --file projects/owa-env-gst/environment_detail.yml
    ```

3. **Install required dependencies**:
    - Install `virtual-uv` package and run `vuv install`. You must run `vuv` instead of `uv` to prevent `uv` from separating virtual environments across sub-repositories in a mono-repo.
    ```sh
    pip install virtual-uv
    vuv install
    ```
    - (Optional) To use raw `uv` binary, you must setup `UV_PROJECT_ENVIRONMENT` environment variable. see [here](https://docs.astral.sh/uv/configuration/environment/#uv_project_environment)
    ```sh
    $ $env:UV_PROJECT_ENVIRONMENT="C:\Users\MilkClouds\miniforge3\envs\owa"
    $ uv sync --inexact
    ```

4. **Import and use core functionality**:
    ```python
    import time

    from owa.registry import CALLABLES, LISTENERS, activate_module

    # Activate the standard environment module
    activate_module("owa.env.std")

    def callback():
        # Get current time in nanoseconds
        time_ns = CALLABLES["clock.time_ns"]()
        print(f"Current time in nanoseconds: {time_ns}")

    # Create a listener for clock/tick event and set interval to 1 seconds.
    tick = LISTENERS["clock/tick"]().configure(interval=1, callback=callback)

    # Start the listener
    tick.start()

    # Allow the listener to run for 2 seconds
    time.sleep(2)

    # Stop the listener and wait for it to finish
    tick.stop(), tick.join()
    ```


## Install from pypi & conda-forge (WIP)

- pypi packages
    - `owa-core`: this package contains only the core logic to manage OWA's EnvPlugin.
    - `owa`: this package contains several base EnvPlugin along with `owa-core`. You must install `gstramer`-related packages in your own.
- conda packages
    - `owa`: this package contains several base EnvPlugin along with `owa-core`.

