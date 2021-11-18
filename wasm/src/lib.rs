mod utils;

use js_sys::JsString;
use shared::normalize;
use wasm_bindgen::prelude::*;

// When the `wee_alloc` feature is enabled, use `wee_alloc` as the global
// allocator.
#[cfg(feature = "wee_alloc")]
#[global_allocator]
static ALLOC: wee_alloc::WeeAlloc = wee_alloc::WeeAlloc::INIT;

#[wasm_bindgen]
pub fn normalize_username(s: &str) -> String {
    utils::set_panic_hook();
    normalize(s)
}


#[wasm_bindgen]
pub fn normalize_username_js_string(s: JsString) -> Result<JsString, JsValue> {
    utils::set_panic_hook();
    if !s.is_valid_utf16() {
        return Err(JsValue::from_str("Invalid utf-16 string"));
    }

    let normalized = normalize(String::from(s).as_str());

    Ok(JsString::from(normalized))
}

