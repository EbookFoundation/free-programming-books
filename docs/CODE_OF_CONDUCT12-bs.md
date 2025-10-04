import React, { useState } from 'react';
import { Shield, Users, AlertCircle, CheckCircle, Mail, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';

export default function CodeOfConduct() {
  const [expandedSection, setExpandedSection] = useState(null);
  const [reportFormOpen, setReportFormOpen] = useState(false);

  const sections = [
    {
      id: 'pledge',
      title: 'Naša Obaveza',
      icon: <Shield className="w-6 h-6" />,
      content: 'Kao kontributori i održavaoci ovog projekta, sa namjerom njegovanja otvorene i pristupačne zajednice, obavezujemo se da ćemo poštovati sve koji daju doprinos kroz prijavljivanje problema, postavljanja zahtjeva za funkcionalnosti, ažuriranje dokumentacije, podnošenje Pull Request-a ili Patche-va, i druge aktivnosti.'
    },
    {
      id: 'standards',
      title: 'Naši Standardi',
      icon: <CheckCircle className="w-6 h-6" />,
      content: 'Posvećeni smo tome da učešće u ovom projektu učinimo iskustvom bez uznemiravanja, bez obzira na nivo iskustva, spol, spolni identitet i izražavanje, seksualnu orijentaciju, invaliditet, lični izgled, veličinu tijela, etničku pripadnost, starost, religiju ili nacionalnost.',
      examples: [
        'Korištenje dobrodošlice i uključivog jezika',
        'Poštovanje različitih perspektiva i iskustava',
        'Prihvatanje konstruktivne kritike',
        'Fokusiranje na ono što je najbolje za zajednicu',
        'Iskazivanje empatije prema drugim članovima zajednice'
      ]
    },
    {
      id: 'unacceptable',
      title: 'Neprihvatljivo Ponašanje',
      icon: <AlertCircle className="w-6 h-6" />,
      content: 'Primjeri neprihvatljivog ponašanja od strane učesnika uključuje:',
      examples: [
        'Upotreba seksualiziranog jezika ili slika',
        'Lični napadi',
        'Provokacije ili uvredljivi/pogrdni komentari',
        'Javno ili privatno uznemiravanje',
        'Objavljivanje tuđih privatnih informacija, poput fizičkih ili elektronskih adresa, bez izričitog dopuštenja',
        'Drugo neetičko ili neprofesionalno ponašanje'
      ]
    },
    {
      id: 'responsibilities',
      title: 'Odgovornosti Održavalaca',
      icon: <Users className="w-6 h-6" />,
      content: 'Održavaoci projekta imaju pravo i odgovornost da uklone, uređuju ili odbiju komentare, commit-e, kôd, wiki ažuriranja, probleme i druge kontribucije koje nisu usklađene sa ovim kodeksom ponašanja, ili privremeno ili trajno zabraniti bilo kojeg kontributora zbog ponašanja koje se smatra neprikladnim, prijetećim ili štetnim.'
    },
    {
      id: 'scope',
      title: 'Opseg Primjene',
      icon: <BookOpen className="w-6 h-6" />,
      content: 'Ovaj kodeks ponašanja se primjenjuje kako unutar projekta tako i u javnim okolnostima kada pojedinac predstavlja projekat ili njegovu zajednicu.'
    }
  ];

  const toggleSection = (id) => {
    setExpandedSection(expandedSection === id ? null : id);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="bg-indigo-600 p-3 rounded-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Kodeks Ponašanja Kontributora</h1>
              <p className="text-gray-600">Contributor Covenant v1.3.0</p>
            </div>
          </div>
          <p className="text-gray-700 leading-relaxed">
            Ovaj kodeks ponašanja definiše standarde i očekivanja za sve učesnike u našoj zajednici, 
            stvarajući siguran i uključiv prostor za saradnju.
          </p>
        </div>

        {/* Sections */}
        {sections.map((section) => (
          <div key={section.id} className="bg-white rounded-xl shadow-md mb-4 overflow-hidden">
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full p-6 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="text-indigo-600">{section.icon}</div>
                <h2 className="text-xl font-semibold text-gray-800">{section.title}</h2>
              </div>
              {expandedSection === section.id ? 
                <ChevronUp className="w-5 h-5 text-gray-600" /> : 
                <ChevronDown className="w-5 h-5 text-gray-600" />
              }
            </button>
            
            {expandedSection === section.id && (
              <div className="px-6 pb-6 border-t border-gray-100">
                <p className="text-gray-700 leading-relaxed mt-4">{section.content}</p>
                {section.examples && (
                  <ul className="mt-4 space-y-2">
                    {section.examples.map((example, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-gray-700">
                        <span className="text-indigo-600 mt-1">•</span>
                        <span>{example}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Enforcement Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-3">
            <Mail className="w-6 h-6 text-indigo-600" />
            Prijavljivanje Incidenata
          </h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            Slučajevi uvredljivog, uznemirujućeg, ili na drugi način neprihvatljivog ponašanja 
            mogu se prijaviti kontaktiranjem voditelja projekta na <strong>victorfelder@gmail.com</strong>
          </p>
          <p className="text-gray-700 leading-relaxed mb-6">
            Sve žalbe će se razmotriti i istražiti, te će rezultovati odgovorom koji se smatra 
            neophodnim i primjerenim okolnostima. Održavaoci su dužni čuvati povjerljivost u pogledu prijavitelja.
          </p>
          
          <button
            onClick={() => setReportFormOpen(!reportFormOpen)}
            className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
          >
            {reportFormOpen ? 'Zatvori Formu' : 'Prijavi Incident'}
          </button>

          {reportFormOpen && (
            <div className="mt-6 p-6 bg-indigo-50 rounded-lg border border-indigo-200">
              <h3 className="font-semibold text-gray-800 mb-4">Forma za Prijavljivanje</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Vaše Ime (Opciono)
                  </label>
                  <input 
                    type="text" 
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Ostavi prazno za anonimno prijavljivanje"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email za Kontakt (Opciono)
                  </label>
                  <input 
                    type="email" 
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="vaš.email@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Opis Incidenta *
                  </label>
                  <textarea 
                    rows="5"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Molimo opišite šta se dogodilo, kada, i ko je bio uključen..."
                  ></textarea>
                </div>
                <p className="text-sm text-gray-600 italic">
                  Napomena: Ovo je primjer forme. Za stvarnu prijavu, molimo kontaktirajte victorfelder@gmail.com
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-white rounded-xl shadow-md p-6 text-center">
          <p className="text-gray-600 text-sm">
            Ovaj kodeks ponašanja je prilagođen iz <strong>Contributor Covenant</strong>, verzija 1.3.0
          </p>
          <a 
            href="https://contributor-covenant.org/version/1/3/0/" 
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-700 text-sm font-medium inline-block mt-2"
          >
            https://contributor-covenant.org/version/1/3/0/
          </a>
        </div>
      </div>
    </div>
  );
}
