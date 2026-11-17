"""Temporal worker with explicit bounded capacity and graceful shutdown."""

import asyncio
import signal
from datetime import timedelta

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from governed_dataops.activities import Activities
from governed_dataops.routing import queue_for_worker
from governed_dataops.settings import Settings, get_settings
from governed_dataops.workflow import IncidentWorkflow


async def create_worker(settings: Settings | None = None) -> Worker:
    settings = settings or get_settings()
    assigned_queue = queue_for_worker(
        settings.task_queue, settings.partition_count, settings.worker_partition
    )
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        data_converter=pydantic_data_converter,
    )
    activities = Activities(settings)
    return Worker(
        client,
        task_queue=assigned_queue,
        workflows=[IncidentWorkflow],
        activities=activities.registered(),
        max_concurrent_activities=settings.worker_concurrency,
        max_concurrent_workflow_tasks=settings.worker_concurrency,
        max_cached_workflows=settings.max_pending_incidents,
        max_activities_per_second=settings.worker_concurrency * 2,
        graceful_shutdown_timeout=timedelta(seconds=30),
        build_id="governed-dataops-0.1.0",
    )


async def run_worker(settings: Settings | None = None) -> None:
    worker = await create_worker(settings)
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    registered = []
    for name in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(name, stopped.set)
            registered.append(name)
        except NotImplementedError:
            pass
    try:
        async with worker:
            await stopped.wait()
    finally:
        for name in registered:
            loop.remove_signal_handler(name)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
