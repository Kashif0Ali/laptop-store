# AK Apple Store inventory and orders

The Excel workbook is the source of truth for laptop details and availability.
Customer order requests are stored in the `orders` table in `chats.db`, with
the product ID and a snapshot of the requested price and quantity. The chat
screens have been replaced by an order form and an admin order list. Previous
chat records are retained in the database.

The storefront reads `laptops.xlsx` and its product photos from one inventory
folder. By default, that folder is the same directory as `app.py`:

- Spreadsheet: `laptops.xlsx`
- Photos: `uploads/`

The seller dashboard at `/admin` shows the exact paths currently in use. The
app creates the spreadsheet with its column headers and creates the photos
folder when they do not exist. Changes are picked up automatically; open
storefront pages check for updates every 15 seconds and reload when inventory
or a linked image changes.

## Add or update a laptop in Excel

Keep the first row as the column headers. Add one laptop per row, with these
columns:

| Column | Value |
| --- | --- |
| ID | Unique product ID, such as `thinkpad-x1-16gb` |
| Brand, Model | Laptop manufacturer and model |
| Processor, Generation | CPU model and generation |
| RAM, SSD, Screen | Memory, storage, and display details |
| Price | Number only; the site formats it as rupees |
| Condition, Availability | For example `Used`, `Available`, or `Out of Stock` |
| Images | Exact photo filename(s) from `uploads/`, separated by commas |
| Description | Product description |

Rows marked `Available`, `In Stock`, or `Yes` are shown and can be requested
through the order form. Requests are cash-on-delivery only; this site does not
process online payments. Customers are sent to WhatsApp with a prefilled order
message to AK Apple Store at `03183703386` and must tap **Send** to notify the
store. This WhatsApp handoff does not send automatically from the server. A
request remains pending until the seller confirms availability, exact
configuration, delivery, and final price. Product prices shown by the site are
indicative.

Review and update orders in the seller dashboard's **View orders** page.

## Add product photos

Copy `.jpg`, `.jpeg`, `.png`, or `.webp` photos into `uploads/`. Enter each
photo's exact filename in the product's `Images` cell, for example:

```text
thinkpad-front.jpg, thinkpad-keyboard.jpg
```

Alternatively, add a laptop and upload its photos through the seller dashboard;
the app stores the images and links them to the product automatically.

The current workbook contains five MacBook listings, marked `Available`.
Prices are labeled indicative and photos are representative; confirm the
exact unit and final details with the customer, and update the listing values
and photos with verified information as stock changes.

## Use a shared or synced folder

Set `INVENTORY_DIR` to a shared local folder or a folder synced by a service such
as iCloud Drive, Dropbox, or OneDrive. That folder must contain `laptops.xlsx`
and an `uploads/` folder. For example, on macOS:

```sh
INVENTORY_DIR="$HOME/Library/CloudStorage/SharedLaptopInventory" ./venv/bin/python app.py
```

When using a custom folder for the first time, the app creates a starter
spreadsheet and `uploads/` there. Share that folder with collaborators, and
have them edit the same workbook and add photos there. Avoid simultaneous
spreadsheet edits to prevent overwriting one another's changes.
