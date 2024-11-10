import pandas as pd
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.exceptions import ValidationError

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            raise ValidationError("No file was provided.")
        
        # Check if the file format is supported
        if not (file.name.endswith('.csv') or file.name.endswith('.xlsx')):
            raise ValidationError("Only .csv and .xlsx files are supported.")

        try:
            # Read the file into a DataFrame
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Ensure the columns are as expected
            required_columns = ['Cust State', 'Cust Pin', 'DPD']
            if not all(column in df.columns for column in required_columns):
                raise ValidationError("File must contain 'Cust State', 'Cust Pin', and 'DPD' columns.")

            # Group by 'Cust State' and aggregate 'DPD' and 'Cust Pin'
            summary_df = df.groupby('Cust State').agg({
                'Cust Pin': lambda x: list(x.unique()),  # Get unique Cust Pins as a list
                'DPD': 'sum'                             # Sum of DPD
            }).reset_index()
            summary_df.columns = ['Cust State', 'Cust Pins', 'Total DPD']

            # Convert the summary DataFrame to a dictionary for the email body
            summary_data = summary_df.to_dict(orient='records')

            # Prepare email content
            email_subject = "Summary Report"
            email_recipient = "rp240502@gmail.com"
            email_body = "Summary Report:\n\n"

            # Add each state summary to the email body
            for record in summary_data:
                cust_state = record['Cust State']
                cust_pins = ", ".join(map(str, record['Cust Pins']))  # Convert list of pins to string
                total_dpd = record['Total DPD']
                email_body += f"Cust State: {cust_state}\n"
                email_body += f"Cust Pins: {cust_pins}\n"
                email_body += f"Total DPD: {total_dpd}\n\n"

            # Send the email
            send_mail(
                subject=email_subject,
                message=email_body,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email_recipient],
                fail_silently=False,
            )

            # Notify the user
            return Response(
                {"message": "Summary report sent via email."},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
