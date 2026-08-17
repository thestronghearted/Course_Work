"""Sales report generation — decomposed (Exercise 12).

The original ``generate_sales_report`` was one ~200-line function handling
validation, filtering, metrics, grouping, three report types, charts and
rendering. It is decomposed here into single-responsibility helpers, with
``generate_sales_report`` acting purely as an orchestrator. Behaviour (and the
exact JSON output) is preserved — verified by the original test suite.
"""

from datetime import datetime


# --- Validation -------------------------------------------------------------

def _validate_inputs(sales_data, report_type, output_format):
    """Raise ValueError if any top-level argument is invalid."""
    if not sales_data or not isinstance(sales_data, list):
        raise ValueError("Sales data must be a non-empty list")
    if report_type not in ['summary', 'detailed', 'forecast']:
        raise ValueError("Report type must be 'summary', 'detailed', or 'forecast'")
    if output_format not in ['pdf', 'excel', 'html', 'json']:
        raise ValueError("Output format must be 'pdf', 'excel', 'html', or 'json'")


def _apply_date_range(sales_data, date_range):
    """Return sales filtered to the inclusive [start, end] date range."""
    if 'start' not in date_range or 'end' not in date_range:
        raise ValueError("Date range must include 'start' and 'end' dates")

    start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
    end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')
    if start_date > end_date:
        raise ValueError("Start date cannot be after end date")

    return [
        sale for sale in sales_data
        if start_date <= datetime.strptime(sale['date'], '%Y-%m-%d') <= end_date
    ]


def _apply_filters(sales_data, filters):
    """Return sales matching every key/value (or key/list-of-values) filter."""
    for key, value in filters.items():
        if isinstance(value, list):
            sales_data = [s for s in sales_data if s.get(key) in value]
        else:
            sales_data = [s for s in sales_data if s.get(key) == value]
    return sales_data


# --- Metrics & grouping -----------------------------------------------------

def _basic_metrics(sales_data):
    """Compute total, average, and max/min sale over the data."""
    total_sales = sum(sale['amount'] for sale in sales_data)
    return {
        'total_sales': total_sales,
        'transaction_count': len(sales_data),
        'average_sale': total_sales / len(sales_data),
        'max_sale': _sale_summary(max(sales_data, key=lambda x: x['amount'])),
        'min_sale': _sale_summary(min(sales_data, key=lambda x: x['amount'])),
    }


def _sale_summary(sale):
    return {'amount': sale['amount'], 'date': sale['date'], 'details': sale}


def _group_sales(sales_data, grouping):
    """Group sales by a field, accumulating count/total/items/average."""
    grouped = {}
    for sale in sales_data:
        key = sale.get(grouping, 'Unknown')
        bucket = grouped.setdefault(key, {'count': 0, 'total': 0, 'items': []})
        bucket['count'] += 1
        bucket['total'] += sale['amount']
        bucket['items'].append(sale)
    for bucket in grouped.values():
        bucket['average'] = bucket['total'] / bucket['count']
    return grouped


# --- Report sections --------------------------------------------------------

def _grouping_section(grouped_data, total_sales, grouping):
    groups = {
        key: {
            'count': data['count'],
            'total': data['total'],
            'average': data['average'],
            'percentage': (data['total'] / total_sales) * 100,
        }
        for key, data in grouped_data.items()
    }
    return {'by': grouping, 'groups': groups}


def _transaction_details(sales_data):
    transactions = []
    for sale in sales_data:
        transaction = dict(sale)
        if 'tax' in sale and 'amount' in sale:
            transaction['pre_tax'] = sale['amount'] - sale['tax']
        if 'cost' in sale and 'amount' in sale:
            transaction['profit'] = sale['amount'] - sale['cost']
            transaction['margin'] = (transaction['profit'] / sale['amount']) * 100
        transactions.append(transaction)
    return transactions


def _forecast_section(sales_data):
    monthly_sales = {}
    for sale in sales_data:
        sale_date = datetime.strptime(sale['date'], '%Y-%m-%d')
        month_key = f"{sale_date.year}-{sale_date.month:02d}"
        monthly_sales[month_key] = monthly_sales.get(month_key, 0) + sale['amount']

    sorted_months = sorted(monthly_sales.keys())
    growth_rates = []
    for i in range(1, len(sorted_months)):
        prev_amount = monthly_sales[sorted_months[i - 1]]
        curr_amount = monthly_sales[sorted_months[i]]
        if prev_amount > 0:
            growth_rates.append(((curr_amount - prev_amount) / prev_amount) * 100)

    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0

    forecast = {}
    if sorted_months:
        last_amount = monthly_sales[sorted_months[-1]]
        year, month = map(int, sorted_months[-1].split('-'))
        for _ in range(1, 4):
            month += 1
            if month > 12:
                month = 1
                year += 1
            last_amount = last_amount * (1 + (avg_growth_rate / 100))
            forecast[f"{year}-{month:02d}"] = last_amount

    return {
        'monthly_sales': monthly_sales,
        'growth_rates': {sorted_months[i]: growth_rates[i - 1] for i in range(1, len(sorted_months))},
        'average_growth_rate': avg_growth_rate,
        'projected_sales': forecast,
    }


def _charts_section(sales_data, grouping, grouped_data):
    date_sales = {}
    for sale in sales_data:
        date_sales[sale['date']] = date_sales.get(sale['date'], 0) + sale['amount']

    charts = {'sales_over_time': {
        'labels': sorted(date_sales.keys()),
        'data': [date_sales[d] for d in sorted(date_sales.keys())],
    }}

    if grouping:
        charts['sales_by_' + grouping] = {
            'labels': list(grouped_data.keys()),
            'data': [data['total'] for data in grouped_data.values()],
        }
    return charts


# --- Rendering --------------------------------------------------------------

def _render(report_data, output_format, include_charts):
    if output_format == 'json':
        return report_data
    if output_format == 'html':
        return _generate_html_report(report_data, include_charts)
    if output_format == 'excel':
        return _generate_excel_report(report_data, include_charts)
    if output_format == 'pdf':
        return _generate_pdf_report(report_data, include_charts)


# --- Orchestrator -----------------------------------------------------------

def generate_sales_report(sales_data, report_type='summary', date_range=None,
                          filters=None, grouping=None, include_charts=False,
                          output_format='pdf'):
    """Generate a sales report. Behaviour identical to the original."""
    _validate_inputs(sales_data, report_type, output_format)

    if date_range:
        sales_data = _apply_date_range(sales_data, date_range)
    if filters:
        sales_data = _apply_filters(sales_data, filters)

    if not sales_data:
        print("Warning: No data matches the specified criteria")
        if output_format == 'json':
            return {"message": "No data matches the specified criteria", "data": []}
        return _generate_empty_report(report_type, output_format)

    metrics = _basic_metrics(sales_data)
    grouped_data = _group_sales(sales_data, grouping) if grouping else {}

    report_data = {
        'report_type': report_type,
        'date_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date_range': date_range,
        'filters': filters,
        'summary': metrics,
    }

    if grouping:
        report_data['grouping'] = _grouping_section(grouped_data, metrics['total_sales'], grouping)
    if report_type == 'detailed':
        report_data['transactions'] = _transaction_details(sales_data)
    if report_type == 'forecast':
        report_data['forecast'] = _forecast_section(sales_data)
    if include_charts:
        report_data['charts'] = _charts_section(sales_data, grouping, grouped_data)

    return _render(report_data, output_format, include_charts)


# --- Unimplemented renderers (unchanged from original) ----------------------

def _generate_empty_report(report_type, output_format):
    pass


def _generate_html_report(report_data, include_charts):
    pass


def _generate_excel_report(report_data, include_charts):
    pass


def _generate_pdf_report(report_data, include_charts):
    pass
