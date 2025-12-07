import streamlit as st
import requests
import logging
from datetime import datetime

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    filename="currency_converter.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# -----------------------------
# Helper function to get rates
# -----------------------------
def get_exchange_rate(base_currency: str, target_currency: str):
    """
    Fetch the latest exchange rate from base_currency to target_currency
    using the open.er-api.com free endpoint.

    Returns:
        (rate, api_time_str) on success
        (None, None) on failure
    """
    url = f"https://open.er-api.com/v6/latest/{base_currency.upper()}"

    try:
        logging.info(
            "Requesting rate from open.er-api.com: base=%s target=%s url=%s",
            base_currency,
            target_currency,
            url,
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        # Example structure:
        # {
        #   "result": "success",
        #   "time_last_update_utc": "Fri, 02 Apr 2020 00:06:37 +0000",
        #   "base_code": "USD",
        #   "rates": {"EUR": 0.919, "GBP": 0.806, ...}
        # }

        if data.get("result") != "success":
            logging.error("API result not success. Full response: %s", data)
            return None, None

        rates = data.get("rates", {})
        rate = rates.get(target_currency.upper())

        if rate is None:
            logging.error(
                "Target currency %s not found in API response. Response: %s",
                target_currency,
                data,
            )
            return None, None

        api_time_str = data.get("time_last_update_utc", "Unknown")
        logging.info(
            "Rate received: 1 %s = %f %s (API time: %s)",
            base_currency,
            rate,
            target_currency,
            api_time_str,
        )

        return rate, api_time_str

    except Exception:
        logging.exception(
            "Error while fetching exchange rate for base=%s target=%s",
            base_currency,
            target_currency,
        )
        return None, None


# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(
    page_title="Currency Converter",
    page_icon="💱",
    layout="centered"
)

st.title("💱 Live Currency Converter")

st.write(
    "Convert between currencies using the latest exchange rates.\n"
    "Example: **GBP → USD** or **EUR → INR**."
)

# Initialise defaults in session_state (so presets can change them)
if "from_currency" not in st.session_state:
    st.session_state.from_currency = "GBP"
if "to_currency" not in st.session_state:
    st.session_state.to_currency = "USD"

# List of currencies
currency_list = [
    "GBP", "USD", "EUR", "INR", "AUD", "CAD", "JPY", "CHF", "CNY"
]

# -----------------------------
# Quick presets
# -----------------------------
preset_map = {
    "Custom": (None, None),
    "GBP → USD (default)": ("GBP", "USD"),
    "USD → GBP": ("USD", "GBP"),
    "EUR → GBP": ("EUR", "GBP"),
    "GBP → INR": ("GBP", "INR"),
    "EUR → USD": ("EUR", "USD"),
}

st.subheader("Quick presets")

preset_label = st.selectbox(
    "Choose a preset pair (or Custom):",
    options=list(preset_map.keys()),
    index=1,  # default: "GBP → USD (default)"
)

base, target = preset_map[preset_label]

if base is not None and target is not None:
    st.session_state.from_currency = base
    st.session_state.to_currency = target

# -----------------------------
# Currency selectors + amount
# -----------------------------
st.subheader("Convert")

col1, col2 = st.columns(2)

with col1:
    from_currency = st.selectbox(
        "From currency",
        options=currency_list,
        index=currency_list.index(st.session_state.from_currency),
        key="from_currency_select",
    )

with col2:
    to_currency = st.selectbox(
        "To currency",
        options=currency_list,
        index=currency_list.index(st.session_state.to_currency),
        key="to_currency_select",
    )

amount = st.number_input(
    "Amount to convert",
    min_value=0.0,
    value=1.0,
    step=1.0
)

if st.button("Convert"):
    if from_currency == to_currency:
        st.warning("Please choose two different currencies.")
    elif amount <= 0:
        st.warning("Please enter an amount greater than zero.")
    else:
        with st.spinner("Fetching latest exchange rate..."):
            rate, api_time = get_exchange_rate(from_currency, to_currency)

        if rate is None:
            st.error("Unable to fetch exchange rate. Please try again later.")
        else:
            converted = amount * rate

            st.success("Conversion successful!")

            st.metric(
                label=f"{amount:.2f} {from_currency} in {to_currency}",
                value=f"{converted:,.4f} {to_currency}",
                delta=f"1 {from_currency} = {rate:.4f} {to_currency}"
            )

            local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            st.caption(
                f"API time (rates last updated): **{api_time}**  \n"
                f"Local fetch time: **{local_time}**  \n"
                "Rates provided by open.er-api.com (ExchangeRate-API Free)."
            )