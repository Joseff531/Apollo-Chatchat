
### Repository Structure
If you would like to contribute code, you need to understand the structure of the repository. This will help you locate the files you want and learn how to submit your code to the repository.

Apollo-Chatchat follows a monorepo organization, and the project's codebase contains multiple packages.

The structure is visualized as a tree below:


```shell
.
├── docker 
├── docs  # documentation 
├── frontend  # frontend
├── libs
│   ├── apollo-chatchat-server  # server
│   │    └── tests
│   │        ├── integration_tests # integration tests (each package has them; omitted elsewhere for brevity)
│   │        └── unit_tests # unit tests (each package has them; omitted elsewhere for brevity)

 

```
The root directory also contains the following files:

pyproject.toml: dependencies for building documentation, documentation linting, and the cookbook.
Makefile: a file containing shortcuts for building, linting, and working with documentation and the cookbook.

There are other files in the root directory as well, but they should all be self-explanatory; please check the respective folders for more information.

### Code

The code in the codebase is divided into two parts:

- The libs/apollo-chatchat-server directory contains the Apollo-Chatchat server-side code.
- The frontend directory contains the Apollo-Chatchat frontend code.

Details follow.
