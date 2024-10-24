def Flexiblejobshopmodel(instance, mdl):
    horizon = 100000
    task_type = collections.namedtuple("task_type", "start end is_present interval")

    all_tasks = {}
    machine_to_intervals = collections.defaultdict(list)
    job_operation_to_intervals = [
        collections.defaultdict(list) for j in range(instance.n)
    ]

    for job in range(instance.n):
        for k in range(instance.o[job]):
            for i in range(instance.g):
                if instance.p[job][k][i] == 0:
                    all_tasks[job, k, i] = []
                else:
                    suffix = "_%i_%i_%i" % (job, k, i)
                    start_var = mdl.NewIntVar(0, horizon, "start" + suffix)
                    end_var = mdl.NewIntVar(0, horizon, "end" + suffix)
                    is_present_var = mdl.NewBoolVar("is_present" + suffix)
                    interval_var = mdl.NewOptionalIntervalVar(
                        start_var,
                        instance.p[job][k][i],
                        end_var,
                        is_present_var,
                        "interval" + suffix,
                    )
                    all_tasks[job, k, i] = task_type(
                        start=start_var,
                        end=end_var,
                        is_present=is_present_var,
                        interval=interval_var,
                    )
                    machine_to_intervals[i].append(interval_var)
                    job_operation_to_intervals[job][k].append(interval_var)

    for i in range(instance.g):
        mdl.AddNoOverlap(machine_to_intervals[i])

    for job in range(instance.n):
        for k in range(instance.o[job]):
            mdl.Add(
                sum(
                    [
                        all_tasks[job, k, i].is_present
                        for i in range(instance.g)
                        if instance.p[job][k][i] > 0
                    ]
                )
                == 1
            )

    for job in range(instance.n):
        for k in range(instance.o[job] - 1):
            for i in range(instance.g):
                for i1 in range(instance.g):
                    if instance.p[job][k + 1][i] > 0 and instance.p[job][k][i1] > 0:
                        mdl.Add(
                            all_tasks[job, k + 1, i].start >= all_tasks[job, k, i1].end
                        )

    # Makespan objective.
    C_max = mdl.NewIntVar(0, horizon, "C_max")
    mdl.AddMaxEquality(
        C_max,
        [
            all_tasks[j, instance.o[j] - 1, i].end
            for j in range(instance.n)
            for i in range(instance.g)
            if instance.p[j][instance.o[j] - 1][i] > 0
        ],
    )
    mdl.Minimize(C_max)

    return mdl
