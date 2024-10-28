import asyncio
async def run_multiple_task(tasks, chunk=5, delay=0):
    runThisTasks = []
    taskIter = iter(tasks)
    allTasksDone = False
    errors = []
    while not allTasksDone:
        try:
            for _ in range(chunk):    
                _task = next(taskIter)
                async def task(t):
                    try:
                        await t
                    except Exception as e:
                        errors.append(e)
                runThisTasks.append(task(_task))
        except (StopAsyncIteration, StopIteration):
            allTasksDone = True
        if runThisTasks:
            await asyncio.sleep(delay)
            await asyncio.gather(*runThisTasks)
        runThisTasks = []
    if errors:
        error = errors[0]
        raise error
