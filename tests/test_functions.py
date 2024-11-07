import unittest
import asyncio
from funcnodes_core.utils.functions import (
    make_run_in_new_thread,
    make_run_in_new_process,
    make_sync_if_needed,
    make_async_if_needed,
    call_sync,
)
import funcnodes_core as fn
import time


def sync_function(x: int) -> int:
    """
    A synchronous function that multiplies the input by 2.
    """
    return x * 2


async def async_function(x: int) -> int:
    """
    An asynchronous function that multiplies the input by 2.
    """
    await asyncio.sleep(0.1)
    return x * 2


async def nested_function(x: int) -> int:
    wrapper_inner = make_run_in_new_thread(sync_function)
    return await wrapper_inner(x)


def failing_function(x: int) -> int:
    raise ValueError("Intentional failure")


@make_run_in_new_thread
def thread_decorated_sync_function(x: int) -> int:
    time.sleep(1)
    return x * 2


@make_run_in_new_process
def process_decorated_sync_function(x: int) -> int:
    time.sleep(1)
    return x * 2


@make_run_in_new_thread
async def thread_decorated_async_function(x: int) -> int:
    await asyncio.sleep(1)
    return x * 2


@make_run_in_new_process
async def process_decorated_async_function(x: int) -> int:
    await asyncio.sleep(1)
    return x * 2


class TestExecutorWrapper(unittest.IsolatedAsyncioTestCase):
    async def test_sync_function_in_thread(self):
        """Test running a synchronous function in a thread."""

        wrapper = make_run_in_new_thread(sync_function)
        result = await wrapper(5)
        self.assertEqual(result, 10)
        wrapper.shutdown()

    async def test_sync_function_in_process(self):
        """Test running a synchronous function in a process."""

        wrapper = make_run_in_new_process(sync_function)
        result = await wrapper(5)
        self.assertEqual(result, 10)
        wrapper.shutdown()

    async def test_async_function_in_thread(self):
        """Test running an asynchronous function in a thread."""

        wrapper = make_run_in_new_thread(async_function)

        result = await wrapper(5)
        self.assertEqual(result, 10)
        wrapper.shutdown()

    async def test_async_function_in_process(self):
        """Test running an asynchronous function in a process."""

        wrapper = make_run_in_new_process(async_function)

        result = await wrapper(5)
        self.assertEqual(result, 10)
        wrapper.shutdown()

    async def test_lambda_function_in_thread(self):
        """Test running a lambda function in a thread."""
        wrapper = make_run_in_new_thread(lambda x: x * 2)

        result = await wrapper(5)
        self.assertEqual(result, 10)
        wrapper.shutdown()

    async def test_lambda_function_in_process(self):
        """Test running a lambda function in a process."""
        wrapper = make_run_in_new_process(lambda x: x * 2)

        result = await wrapper(5)
        self.assertEqual(result, 10)
        wrapper.shutdown()

    async def test_failing_function_in_thread(self):
        """Test a failing function in a thread."""

        wrapper = make_run_in_new_thread(failing_function)

        with self.assertRaises(ValueError):
            await wrapper(5)
        wrapper.shutdown()

    async def test_failing_function_in_process(self):
        """Test a failing function in a process."""

        wrapper = make_run_in_new_process(failing_function)

        with self.assertRaises(ValueError):
            await wrapper(5)
        wrapper.shutdown()

    async def test_make_sync_if_needed_on_async_function(self):
        """Test make_sync_if_needed on an asynchronous function."""

        l_sync_function = make_sync_if_needed(async_function)
        result = l_sync_function(5)
        self.assertEqual(result, 10)

    async def test_make_async_if_needed_on_sync_function(self):
        """Test make_async_if_needed on a synchronous function."""

        l_async_function = make_async_if_needed(sync_function)

        result = await l_async_function(5)
        self.assertEqual(result, 10)

    async def test_make_async_if_needed_on_async_function(self):
        """Test make_async_if_needed on an already asynchronous function."""

        l_async_function = make_async_if_needed(async_function)

        result = await l_async_function(5)
        self.assertEqual(result, 10)

    async def test_make_sync_if_needed_on_sync_function(self):
        """Test make_sync_if_needed on an already synchronous function."""

        l_sync_function = make_sync_if_needed(sync_function)
        result = l_sync_function(5)
        self.assertEqual(result, 10)

    async def test_make_sync_if_needed_on_mixed_functions(self):
        """Test make_sync_if_needed on a mix of coroutine and non-coroutine functions."""

        async_func = make_sync_if_needed(async_function)
        sync_func = make_sync_if_needed(sync_function)

        result_async = async_func(5)
        result_sync = sync_func(5)

        self.assertEqual(result_async, 10)
        self.assertEqual(result_sync, 10)

    async def test_nested_executors(self):
        """Test running an executor inside another executor."""

        wrapper_outer = make_run_in_new_thread(nested_function)
        result = await wrapper_outer(5)
        self.assertEqual(result, 10)
        wrapper_outer.shutdown()

    async def test_call_sync_with_sync_function(self):
        """Test call_sync with a synchronous function."""
        result = call_sync(sync_function, 5)
        self.assertEqual(result, 10)

    async def test_call_sync_with_async_function(self):
        """Test call_sync with an asynchronous function."""
        result = call_sync(async_function, 5)
        self.assertEqual(result, 10)

    async def test_call_sync_with_failing_async_function(self):
        """Test call_sync with an asynchronous function that fails."""

        async def failing_async_function(x: int) -> int:
            await asyncio.sleep(0.1)
            raise ValueError("Intentional async failure")

        with self.assertRaises(ValueError):
            call_sync(failing_async_function, 5)

    async def test_make_run_in_new_thread_with_non_callable(self):
        """Test make_run_in_new_thread with a non-callable object."""
        with self.assertRaises(TypeError):
            make_run_in_new_thread(123)  # Passing an integer instead of a function

    async def test_make_run_in_new_process_with_non_callable(self):
        """Test make_run_in_new_process with a non-callable object."""
        with self.assertRaises(TypeError):
            make_run_in_new_process(
                "not a function"
            )  # Passing a string instead of a function

    async def test_thread_decorated_sync_function(self):
        """Test a synchronous function decorated with make_run_in_new_thread."""
        t = time.time()

        async def stop1():
            return time.time() - t

        result = await asyncio.gather(thread_decorated_sync_function(5), stop1())
        t2 = time.time() - t

        self.assertLess(result[1], 1)
        self.assertEqual(result[0], 10)
        self.assertGreater(t2, 1)

    async def test_process_decorated_sync_function(self):
        """Test a synchronous function decorated with make_run_in_new_process."""
        t = time.time()

        async def stop1():
            return time.time() - t

        result = await asyncio.gather(process_decorated_sync_function(5), stop1())
        t2 = time.time() - t

        print(result, t2)
        self.assertLess(result[1], 1)
        self.assertEqual(result[0], 10)
        self.assertGreater(t2, 1)

    async def test_thread_decorated_async_function(self):
        """Test an asynchronous function decorated with make_run_in_new_thread."""
        t = time.time()

        async def stop1():
            return time.time() - t

        result = await asyncio.gather(thread_decorated_async_function(5), stop1())
        t2 = time.time() - t

        self.assertLess(result[1], 1)
        self.assertEqual(result[0], 10)
        self.assertGreater(t2, 1)

    async def test_process_decorated_async_function(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        t = time.time()

        async def stop1():
            return time.time() - t

        result = await asyncio.gather(process_decorated_async_function(5), stop1())
        t2 = time.time() - t

        self.assertLess(result[1], 1)
        self.assertEqual(result[0], 10)
        self.assertGreater(t2, 1)

    async def test_async_as_node(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_async_as_node",
            separate_process=True,
        )(async_function)()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "An asynchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ProcessExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, async_function)

    async def test_sync_as_node(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_sync_as_node",
            separate_process=True,
        )(sync_function)()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "A synchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ProcessExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, sync_function)

    async def test_async_as_node_thread(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_async_as_node_thread",
            separate_thread=True,
        )(async_function)()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "An asynchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ThreadExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, async_function)

    async def test_sync_as_node_thread(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_sync_as_node_thread",
            separate_thread=True,
        )(sync_function)()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "A synchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ThreadExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, sync_function)

    async def test_async_as_node_dec(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""

        # wraps twice: to make it sync for process and in the executor wrapper
        pf = make_run_in_new_process(async_function)

        node = fn.NodeDecorator(
            node_id="test_async_as_node_dec",
        )(pf)()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "An asynchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__.__wrapped__, fn.utils.functions.ProcessExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.__wrapped__.func, async_function)

    async def test_sync_as_node_dec(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_sync_as_node_dec",
            separate_process=True,
        )(make_run_in_new_process(sync_function))()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "A synchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ProcessExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, sync_function)

    async def test_async_as_node_thread_dec(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_async_as_node_thread_dec",
            separate_thread=True,
        )(make_run_in_new_thread(async_function))()

        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "An asynchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ThreadExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, async_function)

    async def test_sync_as_node_thread_dec(self):
        """Test an asynchronous function decorated with make_run_in_new_process."""
        node = fn.NodeDecorator(
            node_id="test_sync_as_node_thread_dec",
            separate_thread=True,
        )(make_run_in_new_thread(sync_function))()

        print(node.serialize())
        node["x"] = 5
        await node

        self.assertEqual(node["out"].value, 10)
        self.assertEqual(
            node.description, "A synchronous function that multiplies the input by 2."
        )

        self.assertIsInstance(
            node.func.__wrapped__, fn.utils.functions.ThreadExecutorWrapper
        )

        self.assertEqual(node.func.__wrapped__.func, sync_function)
