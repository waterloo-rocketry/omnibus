# Contributing to Omnibus

## Setting Up Your Environment

### Cloning the Repo and Installing Dependencies

Please follow the steps listed in the [README](https://github.com/waterloo-rocketry/omnibus/blob/master/README.md#installation).

## Contributing Code

### Taking Issues

The best way to get started on contributing to Omnibus is to take on an issue. Simply go to the [Software Master Project](https://github.com/orgs/waterloo-rocketry/projects/2), expand the Omnibus section and find an unassigned issue that interests you. Some issues may be lacking context or background info so feel free to DM the current Software Lead or whoever opened the issue for some more info. Once you've found an issue that you would like to work on, then set yourself as the issue's assignee and once ready, change the status of the issue from "Todo" to "In Progress".

### Creating Branches

The repo follows the branch naming convention of `{name}/{issue_num}-{description}`, e.g. `oraazi/157-update-readme-contributing`

- `{name}` is the part of the branch name that identifies its author. Please use your **WatIAM username** (the combination of your first intial, possibly some numbers, and the first few letters of your last name that comes before `@uwaterloo.ca` in your email).
- `{issue_num}` is the issue number of the issue that you are trying to fix or implement. If this branch is not associated with an issue, then you do not need to specify anything for this (e.g., just `oraazi/update-readme-contributing` is fine)
- `{description}` is a short description of what this branch is fixing/implementing. Be sure to keep it short, as good practice is to keep the entire branch name under 30-40 characters.

### Formatting and Linting Your Code

This repo conforms to [PEP8](https://pep8.org) guidelines for Python code. We have a script to automatically enforce these guidelines (`tools/format.sh`). It is **mandatory** to run this before pushing your branch or opening a PR, and *recommended* before every commit.

### Publishing PRs

When you have written your code and are ready to get it reviewed and merged to `master`, then you can [open a PR for your branch](https://github.com/waterloo-rocketry/omnibus/compare). Here's a few things that you should make sure to do when creating your PR:

- All branches being merged to `master` must pass all their unit tests (they are run automatically when you open a PR).
- Assign yourself as the assignee for the PR.
- The default software reviewers and Omnibus codeowners will automatically get requested for review on your PR. You can also request a review from anyone else that you think would be interested in your code.
- Make sure to link the PR to the relevant issue, if possible. The easiest way is [by using keywords in the PR description](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword), e.g. you can link the PR to Issue 157 by writing "closes #157" somewhere in the description.
- Since your task is now in a review state, make sure to move the project status of the issue that this PR is linked to from "In Progress" to "Needs Review". If this project is not linked to an issue, add the PR to the "Software Master Project" Project under Omnibus and set its status accordingly.

### Merging PRs

Once your PR has passed all unit tests, and has been reviewed and approved, you can merge it to `master`. Merge using the "Squash and Merge" option so that all the commits from your branch are "squashed" into one commit containing all the changes. Congrats, you're now free to take on another issue and continue to make Omnibus better! 
