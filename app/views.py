from datetime import datetime

@login_required(login_url = 'login')
def book1(request, id):
    email = request.user.username
    context = {}
    context["start_date"] = ""
    context["end_date"] = ""

    with connection.cursor() as cursor:
        cursor.execute("SELECT hu1.hdb_address, hu1.hdb_unit_number, hu1.price_per_day FROM hdb_units hu1 WHERE hu1.hdb_id = %s", [id])
        row = cursor.fetchone()

    context["hdb_id"] = id
    context["hdb_address"] = row[0]
    context["hdb_unit_number"] = row[1]
    context["booked_by"] = email

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        context["start_date"] = start_date
        context["end_date"] = end_date
        
        try:
            cursor.execute("INSERT INTO bookings(hdb_id, booked_by, start_date, end_date, credit_card_type, credit_card_number)\
                            VALUES (%s, '%s', '%s', '%s', 'mastercard', '2221000000000000')", [id, email, start_date, end_date])
            cursor.execute("DELETE FROM bookings WHERE hdb_id = %s AND booked_by = %s AND start_date = %s AND end_date = %s", [id, email, start_date, end_date])
            
        except Exception as e:
            error = str(e)

            if "Booking Dates Not Available" in error:
                messages.error(request, "Selected dates are not available")

            return render(request, "app/book1.html", context)

        context["total_price"] = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days * row[2]

        return render(request, "app/book2.html", context)

    return render(request, "app/book1.html", context)

@login_required(login_url = 'login')
def book2(request, id, start_date, end_date):
    email = request.user.username
    context = {}

    if request.method == 'POST':
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        hdb_id = request.POST.get("hdb_id")
        hdb_address = request.POST.get("hdb_address")
        hdb_unit_number = request.POST.get("hdb_unit_number")
        card_number = request.POST.get("credit_card_number")
        card_type = request.POST.get("credit_card_type")
        context["start_date"] = start_date
        context["end_date"] = end_date
        context["hdb_id"] = hdb_id
        context["hdb_address"] = hdb_address
        context["hdb_unit_number"] = hdb_unit_number
        context["credit_card_number"] = card_number
        context["credit_card_type"] = card_type
        context["booked_by"] = email
        
        try:
            cursor.execute("INSERT INTO bookings(hdb_id, booked_by, start_date, end_date, credit_card_type, credit_card_number)\
                            VALUES (%s, '%s', '%s', '%s', '%s', '%s')", [id, email, start_date, end_date, card_type, card_number])

        except Exception as e:
            error = str(e)

            if e == 'new row for relation "bookings" violates check constraint "bookings_check1"':
                if card_type == "Mastercard":
                    messages.error(request, "Please input a valid Mastercard number")
                elif card_type == "VISA":
                    messages.error(request, "Please input a valid VISA card number")
                else:
                    messages.error(request, "Please input a valid American Express card number")
            return render(request, "app/book1.html", context)

        messages.success(request, "Successful booking for HDB address {} unit {} from {} to {}".format(row[0], row[1], start_date, end_date))

        return render(request, "app/listings.html", context)
                        
