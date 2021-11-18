use pyo3::prelude::*;
use shared::normalize;

#[pyfunction]
fn normalize_username(s: &str) -> String {
    normalize(s)
}

#[pymodule]
fn normalizer(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(normalize_username, m)?)?;
    Ok(())
}
