# Issues, Feature Requests, Implementation and Integration
In this GitLab instance, we are rather tight on space, so please refrain from uploading files.

## Creating Issues
In order to pinpoint a problem, please provide at least the 
- expected behaviour (What did you want to achieve),
- experienced behaviour (What happend?),
- the function and preferably file and line, which are problemativ (Where is the error?),
- state of your installation (e.g. commit hash, release tag),
- an example to reproduce the error: if not a suitable as inline code, as a link to the file (hosted elsewhere, see top), 
- (optional, but highly appreciated) proposal for a fix

## Feature requests
Feature requests are mostly treated to as Issues. However, since this functionality is not yet present please make clear:
- shortcoming of the current implementation (What is currently impossible?),
- usecase of the requested functionality (How could this be used?),
- proposal of the interface/implementation (How would you expect it to work? How would you implement it?)
- related literature (no uploads, but as link, e.g. DOI, URL or alike)

## Implement features
If you want to contribute by coding, it is highly appreciated. However, to keep it clean, please use the following workflow.
1. Create two new branches: `<working_branch_name>` and `<working_branch_name>_dev`.
2. Create a new Merge Request for `<working_branch_name>` into `master`, see Merge Requests.
3. Work on the `<working_branch_name>_dev` branch. Document everything using `doxygen`. Undocumented code is unusable code and will be rejected, even if the code itself is nice.
4. When you think, you are done, sqaush merge `<working_branch_name>_dev` to `<working_branch_name>`.
5. Tag a reviewer (request review).
6. Wait for review, discuss and implement the remaining problems (got back to 3.).
7. If everything is resolved, `<working_branch_name>` will be merged for you.

## Merge Requests
### Prior to implementation:
It is preferred, that you open a merge request, before starting your work, to keep a track, which issues are already under work.
- Sketch your aims (What do you intent to improve?)
- Link related Issues (Which issues you want to solve?)
- Set yourself as assignee.
- Discussion about conrete issue in dedicated Issues (see Creating Issues), but general conceptional stuff in the Merge Request.

### Prior to integration:
At the latest, you need to update the Merge Request, which issues you solved and what you really did.
- Patch notes (What did you change?). Describe it in such a detail, that is enough to read the merge request to understand everything, that happened.
  But keep it as concise as possible. 
- Related Issues (Which issues are solved?)
- Set a reviewer.
- Discuss review below.

# Contributers
- Max Herbers
- Bertram Richter
