# This file was autogenerated by some hot garbage in the `uniffi` crate.
# Trust me, you don't want to mess with it!

# Common helper code.
#
# Ideally this would live in a separate .py file where it can be unittested etc
# in isolation, and perhaps even published as a re-useable package.
#
# However, it's important that the details of how this helper code works (e.g. the
# way that different builtin types are passed across the FFI) exactly match what's
# expected by the rust code on the other side of the interface. In practice right
# now that means coming from the exact some version of `uniffi` that was used to
# compile the rust component. The easiest way to ensure this is to bundle the Python
# helpers directly inline like we're doing here.

import os
import sys
import ctypes
import enum
import struct
import contextlib
import datetime


class RustBuffer(ctypes.Structure):
    _fields_ = [
        ("capacity", ctypes.c_int32),
        ("len", ctypes.c_int32),
        ("data", ctypes.POINTER(ctypes.c_char)),
    ]

    @staticmethod
    def alloc(size):
        return rust_call(_UniFFILib.ffi_normalizer_c9ab_rustbuffer_alloc, size)

    @staticmethod
    def reserve(rbuf, additional):
        return rust_call(_UniFFILib.ffi_normalizer_c9ab_rustbuffer_reserve, rbuf, additional)

    def free(self):
        return rust_call(_UniFFILib.ffi_normalizer_c9ab_rustbuffer_free, self)

    def __str__(self):
        return "RustBuffer(capacity={}, len={}, data={})".format(
            self.capacity,
            self.len,
            self.data[0:self.len]
        )

    @contextlib.contextmanager
    def allocWithBuilder():
        """Context-manger to allocate a buffer using a RustBufferBuilder.

        The allocated buffer will be automatically freed if an error occurs, ensuring that
        we don't accidentally leak it.
        """
        builder = RustBufferBuilder()
        try:
            yield builder
        except:
            builder.discard()
            raise

    @contextlib.contextmanager
    def consumeWithStream(self):
        """Context-manager to consume a buffer using a RustBufferStream.

        The RustBuffer will be freed once the context-manager exits, ensuring that we don't
        leak it even if an error occurs.
        """
        try:
            s = RustBufferStream(self)
            yield s
            if s.remaining() != 0:
                raise RuntimeError("junk data left in buffer after consuming")
        finally:
            self.free()

    # For every type that lowers into a RustBuffer, we provide helper methods for
    # conveniently doing the lifting and lowering. Putting them on this internal
    # helper object (rather than, say, as methods on the public classes) makes it
    # easier for us to hide these implementation details from consumers, in the face
    # of python's free-for-all type system.

    # The primitive String type.

    @staticmethod
    def allocFromString(value):
        with RustBuffer.allocWithBuilder() as builder:
            builder.write(value.encode("utf-8"))
            return builder.finalize()

    def consumeIntoString(self):
        with self.consumeWithStream() as stream:
            return stream.read(stream.remaining()).decode("utf-8")


class ForeignBytes(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_int32),
        ("data", ctypes.POINTER(ctypes.c_char)),
    ]

    def __str__(self):
        return "ForeignBytes(len={}, data={})".format(self.len, self.data[0:self.len])

class RustBufferStream(object):
    # Helper for structured reading of bytes from a RustBuffer

    def __init__(self, rbuf):
        self.rbuf = rbuf
        self.offset = 0

    def remaining(self):
        return self.rbuf.len - self.offset

    def _unpack_from(self, size, format):
        if self.offset + size > self.rbuf.len:
            raise InternalError("read past end of rust buffer")
        value = struct.unpack(format, self.rbuf.data[self.offset:self.offset+size])[0]
        self.offset += size
        return value

    def read(self, size):
        if self.offset + size > self.rbuf.len:
            raise InternalError("read past end of rust buffer")
        data = self.rbuf.data[self.offset:self.offset+size]
        self.offset += size
        return data

class RustBufferTypeReader(object):
    # For every type used in the interface, we provide helper methods for conveniently
    # reading that type in a buffer. Putting them on this internal helper object (rather
    # than, say, as methods on the public classes) makes it easier for us to hide these
    # implementation details from consumers, in the face of python's free-for-all type
    # system.
    # This class holds the logic for *how* to read the types from a buffer - the buffer itself is
    # always passed in, because the actual buffer might be owned by a different crate/module.

    @staticmethod
    def readString(stream):
        size = stream._unpack_from(4, ">i")
        if size < 0:
            raise InternalError("Unexpected negative string length")
        utf8Bytes = stream.read(size)
        return utf8Bytes.decode("utf-8")

class RustBufferBuilder(object):
    # Helper for structured writing of bytes into a RustBuffer.

    def __init__(self):
        self.rbuf = RustBuffer.alloc(16)
        self.rbuf.len = 0

    def finalize(self):
        rbuf = self.rbuf
        self.rbuf = None
        return rbuf

    def discard(self):
        if self.rbuf is not None:
            rbuf = self.finalize()
            rbuf.free()

    @contextlib.contextmanager
    def _reserve(self, numBytes):
        if self.rbuf.len + numBytes > self.rbuf.capacity:
            self.rbuf = RustBuffer.reserve(self.rbuf, numBytes)
        yield None
        self.rbuf.len += numBytes

    def _pack_into(self, size, format, value):
        with self._reserve(size):
            # XXX TODO: I feel like I should be able to use `struct.pack_into` here but can't figure it out.
            for i, byte in enumerate(struct.pack(format, value)):
                self.rbuf.data[self.rbuf.len + i] = byte

    def write(self, value):
        with self._reserve(len(value)):
            for i, byte in enumerate(value):
                self.rbuf.data[self.rbuf.len + i] = byte

class RustBufferTypeBuilder(object):
    # For every type used in the interface, we provide helper methods for conveniently
    # writing values of that type in a buffer. Putting them on this internal helper object
    # (rather than, say, as methods on the public classes) makes it easier for us to hide
    # these implementation details from consumers, in the face of python's free-for-all
    # type system.
    # This class holds the logic for *how* to write the types to a buffer - the buffer itself is
    # always passed in, because the actual buffer might be owned by a different crate/module.

    @staticmethod
    def writeString(builder, v):
        utf8Bytes = v.encode("utf-8")
        builder._pack_into(4, ">i", len(utf8Bytes))
        builder.write(utf8Bytes)

# Error definitions
class InternalError(Exception):
    pass

class RustCallStatus(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_int8),
        ("error_buf", RustBuffer),
    ]

    # These match the values from the uniffi::rustcalls module
    CALL_SUCCESS = 0
    CALL_ERROR = 1
    CALL_PANIC = 2

    def __str__(self):
        if self.code == RustCallStatus.CALL_SUCCESS:
            return "RustCallStatus(CALL_SUCCESS)"
        elif self.code == RustCallStatus.CALL_ERROR:
            return "RustCallStatus(CALL_ERROR)"
        elif self.code == RustCallStatus.CALL_PANIC:
            return "RustCallStatus(CALL_SUCCESS)"
        else:
            return "RustCallStatus(<invalid code>)"

# Map error classes to the RustBufferTypeBuilder method to read them
_error_class_to_reader_method = {
}

def consume_buffer_into_error(error_class, rust_buffer):
    reader_method = _error_class_to_reader_method[error_class]
    with rust_buffer.consumeWithStream() as stream:
        return reader_method(stream)

def rust_call(fn, *args):
    # Call a rust function
    return rust_call_with_error(None, fn, *args)

def rust_call_with_error(error_class, fn, *args):
    # Call a rust function and handle any errors
    #
    # This function is used for rust calls that return Result<> and therefore can set the CALL_ERROR status code.
    # error_class must be set to the error class that corresponds to the result.
    call_status = RustCallStatus(code=0, error_buf=RustBuffer(0, 0, None))

    args_with_error = args + (ctypes.byref(call_status),)
    result = fn(*args_with_error)
    if call_status.code == RustCallStatus.CALL_SUCCESS:
        return result
    elif call_status.code == RustCallStatus.CALL_ERROR:
        if error_class is None:
            call_status.err_buf.contents.free()
            raise InternalError("rust_call_with_error: CALL_ERROR, but no error class set")
        else:
            raise consume_buffer_into_error(error_class, call_status.error_buf)
    elif call_status.code == RustCallStatus.CALL_PANIC:
        # When the rust code sees a panic, it tries to construct a RustBuffer
        # with the message.  But if that code panics, then it just sends back
        # an empty buffer.
        if call_status.error_buf.len > 0:
            msg = call_status.error_buf.consumeIntoString()
        else:
            msg = "Unknown rust panic"
        raise InternalError(msg)
    else:
        raise InternalError("Invalid RustCallStatus code: {}".format(
            call_status.code))

# This is how we find and load the dynamic library provided by the component.
# For now we just look it up by name.
#
# XXX TODO: This will probably grow some magic for resolving megazording in future.
# E.g. we might start by looking for the named component in `libuniffi.so` and if
# that fails, fall back to loading it separately from `lib${componentName}.so`.

def loadIndirect():
    if sys.platform == "linux":
        libname = "lib{}.so"
    elif sys.platform == "darwin":
        libname = "lib{}.dylib"
    elif sys.platform.startswith("win"):
        # As of python3.8, ctypes does not seem to search $PATH when loading DLLs.
        # We could use `os.add_dll_directory` to configure the search path, but
        # it doesn't feel right to mess with application-wide settings. Let's
        # assume that the `.dll` is next to the `.py` file and load by full path.
        libname = os.path.join(
            os.path.dirname(__file__),
            "{}.dll",
        )
    return getattr(ctypes.cdll, libname.format("uniffi_normalizer"))

# A ctypes library to expose the extern-C FFI definitions.
# This is an implementation detail which will be called internally by the public API.

_UniFFILib = loadIndirect()
_UniFFILib.normalizer_c9ab_normalize_username.argtypes = (
    RustBuffer,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.normalizer_c9ab_normalize_username.restype = RustBuffer
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_alloc.argtypes = (
    ctypes.c_int32,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_alloc.restype = RustBuffer
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_from_bytes.argtypes = (
    ForeignBytes,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_from_bytes.restype = RustBuffer
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_free.argtypes = (
    RustBuffer,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_free.restype = None
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_reserve.argtypes = (
    RustBuffer,
    ctypes.c_int32,
    ctypes.POINTER(RustCallStatus),
)
_UniFFILib.ffi_normalizer_c9ab_rustbuffer_reserve.restype = RustBuffer

# Public interface members begin here.






def normalize_username(s):
    s = s
    _retval = rust_call(_UniFFILib.normalizer_c9ab_normalize_username,RustBuffer.allocFromString(s))
    return _retval.consumeIntoString()





__all__ = [
    "InternalError",
    "normalize_username",
]

