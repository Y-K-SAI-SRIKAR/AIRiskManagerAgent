import asyncio
import os

import httpx
from dotenv import load_dotenv


load_dotenv()


ML_URL = os.getenv(
    "ML_SERVICE_URL"
)


async def main():

    print("ML URL:", ML_URL)

    async with httpx.AsyncClient(
        timeout=120.0
    ) as client:

        # ------------------------------------------------------
        # Health
        # ------------------------------------------------------

        print("\nChecking /health...")

        health = await client.get(
            f"{ML_URL}/health"
        )

        print(
            "Health status:",
            health.status_code
        )

        print(
            "Health response:",
            health.text
        )

        # ------------------------------------------------------
        # Prediction
        # ------------------------------------------------------

        print("\nCalling /predict...")

        payload = {
            "transaction": {
                "TransactionDT": 100000,
                "TransactionAmt": 1000.0,
                "ProductCD": "W",
                "card1": 10000,
                "card2": 111.0,
                "card3": 150.0,
                "card4": "visa",
                "card5": 226.0,
                "card6": "credit",
                "addr1": 100,
                "addr2": 10,
                "dist1": 10.0,
                "P_emaildomain": "gmail.com",
                "R_emaildomain": "gmail.com",

                "C2": 1.0,
                "C3": 1.0,
                "C9": 1.0,
                "D1": 10.0,
                "D3": 5.0,
                "D5": 5.0,
                "D11": 10.0,
                "D15": 10.0,

                "M1": "T",
                "M2": "T",
                "M3": "T",
                "M4": "M0",
                "M5": "F",
                "M6": "F",
                "M7": "F",
                "M8": "F",
                "M9": "F",

                "V1": 1.0,
                "V3": 1.0,
                "V5": 1.0,
                "V6": 1.0,
                "V12": 1.0,
                "V14": 1.0,
                "V20": 1.0,
                "V23": 1.0,
                "V26": 1.0,
                "V29": 1.0,
                "V35": 1.0,
                "V38": 1.0,
                "V41": 1.0,
                "V45": 1.0,
                "V47": 1.0,
                "V52": 1.0,
                "V53": 1.0,
                "V56": 1.0,
                "V62": 1.0,
                "V65": 1.0,
                "V67": 1.0,
                "V68": 1.0,
                "V83": 1.0,
                "V86": 1.0,
                "V89": 1.0,
                "V107": 1.0,
                "V111": 1.0,
                "V117": 1.0,
                "V120": 1.0,
                "V123": 1.0,
                "V169": 1.0,
                "V173": 1.0,
                "V174": 1.0,
                "V197": 1.0,
                "V199": 1.0,
                "V220": 1.0,
                "V222": 1.0,
                "V223": 1.0,
                "V235": 1.0,
                "V239": 1.0,
                "V240": 1.0,
                "V247": 1.0,
                "V257": 1.0,
                "V262": 1.0,
                "V271": 1.0,
                "V281": 1.0,
                "V283": 1.0,
                "V284": 1.0,
                "V286": 1.0,
                "V287": 1.0,
                "V289": 1.0,
                "V290": 1.0,
                "V301": 1.0,
                "V302": 1.0,
                "V305": 1.0,
                "V312": 1.0,
                "V315": 1.0,

                "id_01": 10.0,
                "id_02": 100.0,
                "id_05": 1.0,
                "id_06": 1.0,
                "id_11": 100.0,
                "id_12": "Found",
                "id_13": 10.0,
                "id_15": "Found",
                "id_16": "Found",
                "id_17": 10.0,
                "id_19": 100.0,
                "id_20": 100.0,
                "id_28": "Found",
                "id_29": "Found",
                "id_31": "chrome",
                "id_35": "T",
                "id_36": "F",
                "id_37": "T",
                "id_38": "F",

                "TransactionHour": 20,
                "TransactionDay": 28,
                "TransactionWeek": 35,
                "TransactionWeekday": 4,
                "TransactionAmt_Log": 6.90875477931522,
                "card1_freq": 1.0,
                "EmailDomainMatch": 1,
                "P_email_Missing": 0,
                "R_email_Missing": 0,
                "CardType": "credit",
            }
        }

        response = await client.post(
            f"{ML_URL}/predict",
            json=payload,
        )

        print(
            "\nPrediction status:",
            response.status_code
        )

        print(
            "Prediction response:"
        )

        print(response.text)


if __name__ == "__main__":
    asyncio.run(main())