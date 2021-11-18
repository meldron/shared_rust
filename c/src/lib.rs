use shared::normalize;
use std::{
    ffi::{CStr, CString},
    os::raw::c_char,
};

#[no_mangle]
pub extern "C" fn normalize_username(p: *const c_char) -> *const c_char {
    let raw = unsafe { CStr::from_ptr(p) };
    let s = raw.to_str().expect("invalid utf-8");

    let normalized = normalize(s);

    let c_string = CString::new(normalized).expect("could not build c string");

    let ptr = c_string.as_ptr();
    std::mem::forget(c_string);

    ptr
}
