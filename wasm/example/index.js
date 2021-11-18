import * as wasm from "wasm";

const withEmoji = "Rust Meetup 🦀";
const invalidUtf16 = withEmoji.substr(0, 13);

const invalidNormalization = wasm.normalize_username(invalidUtf16);
console.log(invalidNormalization);

try {
    wasm.normalize_username_js_string(invalidUtf16);
} catch (err) {
    console.error(`Error normalizing '${invalidUtf16}': ${err}`);
}
