# coding=utf-8
from __future__ import print_function

import io
import os.path

import jinja2

from piecash import open_book

if __name__ == '__main__':
    this_folder = os.path.dirname(os.path.realpath(__file__))

    with open_book(os.path.join(this_folder, "..", "gnucash_books", "CGT2015.gnucash"), open_if_lock=True) as book:
        transactions = book.transactions

        env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
        xml = env.from_string(u"""
<?xml version="1.0"?>
<comptabilite>
  <exercice>
    <DateCloture>2016-12-31T00:00:00</DateCloture>
    <journal>
      <JournalCode>Le code du Journal</JournalCode>
      <JournalLib>Le libellé du Journal</JournalLib>
      {% for i, ecriture in enumerate(transactions) %}
      <ecriture>
        <EcritureNum>{{ i }}</EcritureNum>
        <EcritureDate>{{ ecriture.post_date.strftime("%Y-%m-%d") }}</EcritureDate>
        <EcritureLib>{{ ecriture.description }}</EcritureLib>
        <PieceRef>{{ ecriture.num }}</PieceRef>
        <PieceDate>{{ ecriture.post_date.strftime("%Y-%m-%d") }}</PieceDate>
        <ValidDate>{{ ecriture.post_date.strftime("%Y-%m-%d") }}</ValidDate>
        {% for sp in ecriture.splits %}
        <ligne>
          <CompteNum>{{ sp.account.code }}</CompteNum>
          <CompteLib>{{ sp.account.name }}</CompteLib>
          <CompteAuxNum>Le numéro de compte auxiliaire (à blanc si non utilisé)</CompteAuxNum>
          <CompteAuxLib>Le libellé de compte auxiliaire (à blanc si non utilisé)</CompteAuxLib>
          <Montantdevise></Montantdevise>
          <Montant>{{ abs(sp.value) }}</Montant>
          <Sens>{% if sp.value >0 %}c{% else %}d{% endif %}</Sens>
        </ligne>
        {% endfor %}
      </ecriture>
      {% endfor %}
    </journal>
  </exercice>
</comptabilite>
        """).render(transactions=transactions,
                    enumerate=enumerate,
                    abs=abs,
                    )

        with io.open("resultat.xml", "w", encoding="utf-8") as f:
            f.write(xml)

# pour référence, fichier généré à partir du xsd
"""
<?xml version="1.0"?>
<comptabilite>
  <exercice>
    <DateCloture>2007-10-26T08:36:28</DateCloture>
    <!--1 or more repetitions:-->
    <journal>
      <JournalCode>string</JournalCode>
      <JournalLib>string</JournalLib>
      <!--Zero or more repetitions:-->
      <ecriture>
        <EcritureNum>string</EcritureNum>
        <EcritureDate>2014-06-09+02:00</EcritureDate>
        <EcritureLib>string</EcritureLib>
        <PieceRef>string</PieceRef>
        <PieceDate>2009-05-16T14:42:28</PieceDate>
        <!--Optional:-->
        <EcritureLet>string</EcritureLet>
        <!--Optional:-->
        <DateLet>2002-11-05T09:01:03+01:00</DateLet>
        <ValidDate>2016-01-01T20:07:42</ValidDate>
        <!--2 or more repetitions:-->
        <ligne>
          <CompteNum>string</CompteNum>
          <CompteLib>string</CompteLib>
          <!--You have a CHOICE of the next 2 items at this level-->
          <!--Optional:-->
          <CompAuxNum>string</CompAuxNum>
          <!--Optional:-->
          <CompteAuxNum>string</CompteAuxNum>
          <!--You have a CHOICE of the next 2 items at this level-->
          <!--Optional:-->
          <CompAuxLib>string</CompAuxLib>
          <!--Optional:-->
          <CompteAuxLib>string</CompteAuxLib>
          <!--Optional:-->
          <Montantdevise>string</Montantdevise>
          <!--Optional:-->
          <Idevise>string</Idevise>
          <!--You have a CHOICE of the next 3 items at this level-->
          <Debit>1.5E2</Debit>
          <Credit>1.5E2</Credit>
          <Montant>1.5E2</Montant>
          <Sens>c</Sens>
          <!--You may enter ANY elements at this point-->
          <AnyElement/>
        </ligne>
        <ligne>
          <CompteNum>string</CompteNum>
          <CompteLib>string</CompteLib>
          <!--You have a CHOICE of the next 2 items at this level-->
          <!--Optional:-->
          <CompAuxNum>string</CompAuxNum>
          <!--Optional:-->
          <CompteAuxNum>string</CompteAuxNum>
          <!--You have a CHOICE of the next 2 items at this level-->
          <!--Optional:-->
          <CompAuxLib>string</CompAuxLib>
          <!--Optional:-->
          <CompteAuxLib>string</CompteAuxLib>
          <!--Optional:-->
          <Montantdevise>string</Montantdevise>
          <!--Optional:-->
          <Idevise>string</Idevise>
          <!--You have a CHOICE of the next 3 items at this level-->
          <Debit>1.5E2</Debit>
          <Credit>1.5E2</Credit>
          <Montant>1.5E2</Montant>
          <Sens>c</Sens>
          <!--You may enter ANY elements at this point-->
          <AnyElement/>
        </ligne>
      </ecriture>
    </journal>
  </exercice>
</comptabilite>
"""
