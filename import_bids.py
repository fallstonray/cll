"""
Notion Bid Import Script
========================
1. Export your Notion bid database as CSV.
2. Rename columns to match the names in COL_MAP below (or update COL_MAP to
   match your Notion column names).
3. Save the file as  bids_import.csv  in the same folder as this script.
4. Run:  python import_bids.py

The script will DELETE all existing bids and replace them with the CSV data.
Run a dry-run first:  python import_bids.py --dry-run
"""

import os
import sys
import csv
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cll.settings')
django.setup()

from landscape.models import Bid
from maintenance.models import Customer
from employee.models import Employee

# ── Column mapping ────────────────────────────────────────────────────────────
# Key   = the model field name (do not change)
# Value = the column header in YOUR CSV (edit these to match Notion export)
COL_MAP = {
    'project_name':   'project_name',
    'customer':       'customer',
    'location':       'location',
    'city':           '',               # not in Notion export — leave blank
    'state':          'state',               
    'zip':            '',               # not in Notion export — leave blank
    'amount':         'amount',
    'estimator':      'estimator',
    'phase':          'phase',
    'status':         'status',
    'bid_submitted':  'bid_submitted',
    'last_contact':   'last_contact_date',
    'next_follow_up': 'next_follow_up',
    'start_date':     'start_date',
    'end_date':       'end_date',
    'notes':          'notes',
    'follow_up_notes':'follow_up_notes',
    'contract_signed':'contract',
}

VALID_PHASES = {'estimating', 'submitted', 'on_hold', 'likely', 'awarded', 'lost', 'dead'}
VALID_STATUSES = {'in_progress', 'scheduled', 'paused', 'delayed', 'completed', 'waiting'}
CSV_FILE = os.path.join(os.path.dirname(__file__), 'bids_import.csv')


def open_csv(path):
    """Open the CSV with automatic encoding and delimiter detection."""
    encodings = ('utf-8-sig', 'utf-16', 'utf-8')
    delimiters = (',', '\t')
    for enc in encodings:
        for delim in delimiters:
            try:
                with open(path, newline='', encoding=enc) as f:
                    reader = csv.DictReader(f, delimiter=delim)
                    rows = list(reader)
                # Sanity check: if the whole header is one column, wrong delimiter
                if rows and len(rows[0]) > 1:
                    return rows, enc, delim
            except (UnicodeDecodeError, UnicodeError):
                break  # wrong encoding — try next encoding
    raise ValueError(f"Could not decode {path}. Try re-saving the CSV as UTF-8 comma-separated.")


def parse_date(value):
    """Accept YYYY-MM-DD, MM/DD/YYYY, or M/D/YYYY."""
    if not value or not value.strip():
        return None
    value = value.strip()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%-m/%-d/%Y'):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    print(f"  ⚠  Could not parse date: '{value}' — leaving blank")
    return None


def parse_bool(value):
    """Convert Yes/No (or True/False/1/0) to a Python bool."""
    return value.strip().lower() in ('yes', 'true', '1', 'checked', '✓') if value else False


def parse_amount(value):
    """Strip $, commas, spaces and convert to float."""
    if not value or not value.strip():
        return None
    cleaned = value.strip().replace('$', '').replace(',', '').replace(' ', '')
    try:
        return float(cleaned)
    except ValueError:
        print(f"  ⚠  Could not parse amount: '{value}' — leaving blank")
        return None


def get(row, field):
    """Safely get a value from the row using the column mapping."""
    col = COL_MAP.get(field)
    if not col:
        return ''
    return row.get(col, '').strip()


def main():
    dry_run = '--dry-run' in sys.argv

    if not os.path.exists(CSV_FILE):
        print(f"❌  File not found: {CSV_FILE}")
        print("    Place your exported CSV at the project root as  bids_import.csv")
        sys.exit(1)

    # ── Load CSV ──────────────────────────────────────────────────────────────
    try:
        rows, detected_enc, detected_delim = open_csv(CSV_FILE)
    except ValueError as e:
        print(f"❌  {e}")
        sys.exit(1)

    delim_name = 'tab-separated' if detected_delim == '\t' else 'comma-separated'
    print(f"📄  Found {len(rows)} rows in {CSV_FILE} (encoding: {detected_enc}, {delim_name})")
    if dry_run:
        print("🔍  DRY RUN — no changes will be made\n")

    # ── Build lookup caches ───────────────────────────────────────────────────
    customers = {c.name.lower(): c for c in Customer.objects.all()}
    employees = {
        f"{e.first_name.lower()} {e.last_name.lower()}": e
        for e in Employee.objects.all()
    }

    # ── Validate column mapping ───────────────────────────────────────────────
    # Strip None keys (trailing commas in header) and whitespace from column names
    actual_cols = {k.strip() for k in (rows[0].keys() if rows else []) if k is not None}

    print(f"    Columns found in CSV: {sorted(actual_cols)}\n")

    missing_required = []
    if COL_MAP['project_name'] not in actual_cols:
        missing_required.append(COL_MAP['project_name'])
    if missing_required:
        print(f"❌  Required column(s) not found in CSV: {missing_required}")
        print(f"    Update COL_MAP in import_bids.py so 'project_name' maps to your actual column name.")
        sys.exit(1)

    print(f"✅  CSV columns look good\n")

    # ── Delete existing bids ──────────────────────────────────────────────────
    if not dry_run:
        count, _ = Bid.objects.all().delete()
        print(f"🗑   Deleted {count} existing bids\n")
    else:
        print(f"🗑   Would delete {Bid.objects.count()} existing bids\n")

    # ── Import ────────────────────────────────────────────────────────────────
    imported = 0
    skipped  = 0
    warnings = []

    for i, row in enumerate(rows, start=2):  # row 2 = first data row
        project_name = get(row, 'project_name')
        if not project_name:
            warnings.append(f"Row {i}: blank project_name — skipped")
            skipped += 1
            continue

        # Customer lookup
        customer_name = get(row, 'customer')
        customer = customers.get(customer_name.lower()) if customer_name else None
        if customer_name and not customer:
            warnings.append(f"Row {i} '{project_name}': customer '{customer_name}' not found — set to blank")

        # Estimator lookup
        estimator_name = get(row, 'estimator')
        estimator = employees.get(estimator_name.lower()) if estimator_name else None
        if estimator_name and not estimator:
            warnings.append(f"Row {i} '{project_name}': estimator '{estimator_name}' not found — set to blank")

        # Phase
        phase = get(row, 'phase').lower().replace(' ', '_')
        if phase not in VALID_PHASES:
            if phase:
                warnings.append(f"Row {i} '{project_name}': invalid phase '{phase}' — defaulting to 'estimating'")
            phase = 'estimating'

        # Status
        status = get(row, 'status').lower().replace(' ', '_')
        if status not in VALID_STATUSES:
            status = None

        # State
        state = get(row, 'state').upper() or 'MD'

        if dry_run:
            print(f"  ✓  [{i}] {project_name} | {customer_name or '—'} | {phase}")
            imported += 1
            continue

        Bid.objects.create(
            project_name    = project_name,
            customer        = customer,
            location        = get(row, 'location') or None,
            city            = get(row, 'city') or None,
            state           = state,
            zip             = get(row, 'zip') or None,
            amount          = parse_amount(get(row, 'amount')),
            estimator       = estimator,
            phase           = phase,
            status          = status or None,
            bid_submitted   = parse_date(get(row, 'bid_submitted')),
            last_contact    = parse_date(get(row, 'last_contact')),
            next_follow_up  = parse_date(get(row, 'next_follow_up')),
            start_date      = parse_date(get(row, 'start_date')),
            end_date        = parse_date(get(row, 'end_date')),
            contract_signed = parse_bool(get(row, 'contract_signed')),
            notes           = get(row, 'notes') or None,
            follow_up_notes = get(row, 'follow_up_notes') or None,
        )
        imported += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'─'*50}")
    if dry_run:
        print(f"DRY RUN complete — {imported} rows would be imported, {skipped} skipped")
    else:
        print(f"✅  Import complete: {imported} bids imported, {skipped} skipped")

    if warnings:
        print(f"\n⚠  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"   • {w}")
    else:
        print("   No warnings.")

    if not dry_run:
        print(f"\n   Total bids in DB: {Bid.objects.count()}")


if __name__ == '__main__':
    main()
