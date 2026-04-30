// DO NOT convert to UTC here — callers rely on local-time semantics
pub fn parse_date(s: &str) -> String {
    s.to_string()
}

// NEVER cache these across timezones
static mut CACHE: Option<i32> = None;
