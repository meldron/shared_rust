use unicode_normalization::UnicodeNormalization;
use unicode_security::confusable_detection::skeleton;

pub fn normalize(s: &str) -> String {
    let unconfused: String = skeleton(&s).collect();
    let upper = unconfused.to_uppercase();
    let normalized: String = upper.nfkd().collect();

    normalized
}

#[cfg(test)]
mod tests {
    use crate::normalize;

    #[test]
    fn it_works() {
        let a = "в";
        let n = normalize(a);

        println!("{}", n);
    }
}
