# Instances
This folder contains all benchmark instances.

## Machine scheduling instances 

This repository contains the machine scheduling instances from Naderi et al. (2023),
taken from https://github.com/INFORMSJoC/2021.0326/tree/15b70e43d230fc7581bdaa1cb37139b5adaf842b/data.

The following changes were made:

- Removed:
  - `Jobshop_Strange`
  - `Distributedflowshop`
  - `OpenShop_strange`
  - `Openshop`

- Modified:
    - `Flexiblejobshop`: Here we moved all instances out of the nested folders `OldBenchmarks` and `New`. The instances in `New` are renamed from `{idx}.txt` to `{idx+193}.txt`, because `OldBenchmarks` has 193 number of instances.
    - `Jobshop`: Here we moved all instances out of the nested folders `Taillard` and `New`. The instances in `New` are renamed from `{idx}.txt` to `{idx+80}.txt`, because `Taillard` has the 80 instances.

## Project scheduling instances
All instances were taken from https://www.projectmanagement.ugent.be/research/data.

- `RCPSP`
  - RG300
  - PSPLIB
- `MMRCPSP`: 
  - MPLIB50
  - MPLIB100
- `RCMPSP`
  - MPLIB1 set 3 
  - Van Eynde
  - Bredael 
    - makespan

- Solutions for RCPSP and MMRCPSP: http://solutionsupdate.ugent.be/index.php/solutions-update?page=0

- http://solutionsupdate.ugent.be/index.php/rcpsp (bks 2024)
