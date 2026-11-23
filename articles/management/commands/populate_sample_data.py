import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import AuthorProfile, AuthorApplication
from articles.models import Category, Tag, Article, ArticleImage, ArticleReview
from reader_features.models import Bookmark, ReadingHistory, AuthorFollow, Comment, ArticleReport, Notification
from analytics.models import ArticleView

User = get_user_model()


class Command(BaseCommand):
    help = "Populate INKLINE with realistic editorial sample categories, authors, readers, articles, and reviews."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Beginning INKLINE editorial database initialization..."))

        # 1. Categories
        categories_data = [
            ("Technology", "technology", "In-depth explorations into computing, algorithmic systems, robotics, and cybernetics.", "bi-cpu", "#2563EB", 1),
            ("Business & Markets", "business", "Macroeconomic analysis, venture capital trends, and corporate governance.", "bi-briefcase", "#059669", 2),
            ("Science", "science", "Astrophysics, clean energy transitions, molecular genetics, and planetary ecology.", "bi-radioactive", "#0891B2", 3),
            ("Education", "education", "Pedagogical revolutions, digital universities, cognitive science, and knowledge access.", "bi-book", "#7C3AED", 4),
            ("Travel & Culture", "culture", "Global architecture, regional literature, anthropological dispatches, and culinary heritage.", "bi-compass", "#800020", 5),
            ("Lifestyle", "lifestyle", "Design theory, modern urbanism, psychological wellness, and daily rituals.", "bi-cup-hot", "#D97706", 6),
            ("Entertainment", "entertainment", "Film aesthetics, contemporary music, independent theater, and the digital arts.", "bi-film", "#DB2777", 7),
            ("Sports & Athletics", "sports", "The sociology of athletics, competitive strategy, physiology, and sporting ethics.", "bi-trophy", "#DC2626", 8),
        ]

        created_categories = {}
        for name, slug, desc, icon, color, order in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': desc,
                    'icon': icon,
                    'accent_color': color,
                    'order': order,
                    'is_active': True
                }
            )
            created_categories[slug] = cat
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(created_categories)} editorial categories."))

        # 2. Tags
        tags_data = [
            "artificial-intelligence", "global-trade", "climate-science", "architecture",
            "neuroscience", "clean-energy", "philosophy", "macroeconomics", "urban-planning", "digital-privacy"
        ]
        created_tags = {}
        for t_name in tags_data:
            tag, _ = Tag.objects.get_or_create(name=t_name)
            created_tags[t_name] = tag

        # 3. Administrator Account
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                'email': "editor.in.chief@inkline.press",
                'first_name': "Julian",
                'last_name': "Vane (Editor-in-Chief)",
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_email_verified': True
            }
        )
        admin_user.set_password("AdminPassword123!")
        admin_user.save()

        # 4. Author Accounts & Profiles
        authors_data = [
            {
                'username': 'maya_lin',
                'email': 'maya.lin@inkline.press',
                'first_name': 'Dr. Maya',
                'last_name': 'Lin',
                'pen_name': 'Dr. Maya Lin',
                'tagline': 'Lead Computing & Neural Systems Investigator',
                'bio': 'Maya Lin holds a doctorate in machine intelligence and writes on large foundation architectures, digital ethics, and computational biology.',
                'interests': 'Artificial Intelligence, Cognitive Systems, Semiconductor Geopolitics',
            },
            {
                'username': 'julian_sterling',
                'email': 'julian.sterling@inkline.press',
                'first_name': 'Julian',
                'last_name': 'Sterling',
                'pen_name': 'Julian Sterling',
                'tagline': 'Senior Economics & Trade Columnist',
                'bio': 'Formerly with the International Monetary Monitor, Julian covers central banking, supply chain reshoring, and the economics of energy transitions.',
                'interests': 'Macroeconomics, Energy Geopolitics, Financial Regulation',
            },
            {
                'username': 'elena_rostova',
                'email': 'elena.rostova@inkline.press',
                'first_name': 'Elena',
                'last_name': 'Rostova',
                'pen_name': 'Elena Rostova',
                'tagline': 'Architecture & Cultural Geographer',
                'bio': 'Elena explores how physical civic space shapes human society. Her essays have received multiple independent journalism fellowships.',
                'interests': 'Urban Architecture, Heritage Conservation, Civic Design',
            }
        ]

        created_authors = []
        for a_data in authors_data:
            auth_u, _ = User.objects.get_or_create(
                username=a_data['username'],
                defaults={
                    'email': a_data['email'],
                    'first_name': a_data['first_name'],
                    'last_name': a_data['last_name'],
                    'role': User.Role.AUTHOR,
                    'is_staff': False,
                    'is_superuser': False,
                    'is_email_verified': True
                }
            )
            auth_u.set_password("AuthorPassword123!")
            auth_u.save()

            AuthorProfile.objects.update_or_create(
                user=auth_u,
                defaults={
                    'pen_name': a_data['pen_name'],
                    'tagline': a_data['tagline'],
                    'bio': a_data['bio'],
                    'writing_interests': a_data['interests'],
                    'is_approved': True,
                    'approved_at': timezone.now() - timedelta(days=60),
                }
            )
            created_authors.append(auth_u)

        # 5. Readers
        readers_data = [
            ("clara_b", "clara@example.com", "Clara", "Barton"),
            ("marcus_a", "marcus@example.com", "Marcus", "Aurelius"),
            ("sophia_t", "sophia@example.com", "Sophia", "Tan"),
        ]
        created_readers = []
        for u_name, email, f_name, l_name in readers_data:
            reader_u, _ = User.objects.get_or_create(
                username=u_name,
                defaults={
                    'email': email,
                    'first_name': f_name,
                    'last_name': l_name,
                    'role': User.Role.READER,
                    'is_staff': False,
                    'is_superuser': False,
                    'is_email_verified': True
                }
            )
            reader_u.set_password("ReaderPassword123!")
            reader_u.save()
            created_readers.append(reader_u)

        # 6. Author Applications (1 Pending for admin queue demonstration)
        AuthorApplication.objects.get_or_create(
            user=created_readers[0],
            defaults={
                'full_name': "Clara Barton",
                'bio': "Investigative medical researcher with 8 years documenting clinical trial data and hospital supply logistics.",
                'writing_interests': "Healthcare Economics, Biotech Infrastructure, Public Health",
                'experience_years': 8,
                'portfolio_url': "https://clarabarton-reporting.org",
                'sample_writing': "Over three years across ten major hospital networks, our telemetry indicates severe fractures in pharmaceutical cold-chain resilience. What began as localized inventory delays has manifested as systemic treatment pauses...",
                'status': AuthorApplication.Status.PENDING,
            }
        )

        # 7. Articles Data
        sample_articles_data = [
            {
                'title': "The Silence of the Supercomputers: Why Modern AI is Moving to the Edge",
                'subtitle': "As hyperscale data centers reach thermodynamic thresholds, a paradigm shift toward localized neuromorphic silicon is transforming real-time cognition.",
                'slug': "silence-of-the-supercomputers-edge-ai",
                'author': created_authors[0],
                'category': created_categories['technology'],
                'article_type': Article.ArticleType.LONGFORM,
                'status': Article.ArticleStatus.PUBLISHED,
                'is_featured': True,
                'is_editors_pick': True,
                'excerpt': "Inside the subterranean computing chambers of Northern Europe, engineers are encountering the unyielding laws of physics: gigawatt power draws and cooling limits that dictate the future of human cognition.",
                'content': """
<p class="lead">Inside the subterranean computing chambers outside Luleå, where glacial rivers power banks of humming accelerator racks, engineers are encountering an unyielding boundary. It is not algorithmic insufficiency or lack of parameters, but the fundamental thermodynamic cost of shuffling electrons across thousands of meters of copper interconnects.</p>

<h3>The Terawatt Bottleneck</h3>
<p>For half a decade, the consensus in artificial intelligence was unsparingly monolithic: scale solves everything. Double the cluster size, multiply the context window, and downstream emergent reasoning follows with mathematical inevitability. Yet, as individual training runs approach the electrical consumption of mid-sized industrialized cities, the calculus has irrevocably shifted.</p>

<blockquote>"We reached the point where the limiting reagent of intelligence is no longer token availability, but the copper wire that connects the memory controller to the arithmetic logic unit."</blockquote>

<p>The emerging discipline of neuromorphic edge processing is upending this centralized architecture. By colocation of non-volatile analog memory alongside ultra-low-power spiking neural cores, micro-devices can now infer complex temporal patterns on milliwatt power budgets. Instead of streaming video feeds back to cloud repositories, perception happens at the sensor's physical diaphragm.</p>

<h3>The Civic Repercussions</h3>
<p>Beyond engineering elegance, edge computing carries immense political consequences. In a centralized paradigm, sovereign authority over informational synthesis rests with a handful of hyperscale infrastructure operators. In an edge-distributed environment, sovereign synthesis returns to the local perimeter: municipal water monitoring, domestic health telemetry, and private linguistic models that never transmit a single byte across an external boundary.</p>

<p>As we look toward the next generation of computing, the monumentality of the cloud may soon look like the steam engines of the nineteenth century—magnificent, gargantuan, and destined to be superseded by the silent, localized currents of the edge.</p>
""",
                'estimated_reading_time': 5,
                'views_count': 412,
                'tags': [created_tags['artificial-intelligence'], created_tags['digital-privacy']],
                'sources': "Stanford HAI Energy Report 2024; IEEE Microelectronics Journal Vol. 48; Interview with Nordic Computing Consortium."
            },
            {
                'title': "The Architecture of Solitude: How Modern Cities Unlearned the Art of Public Gathering",
                'subtitle': "From hostile street benches to privatized plazas, the slow death of third spaces has eroded our civic fabric.",
                'slug': "architecture-of-solitude-public-gathering",
                'author': created_authors[2],
                'category': created_categories['culture'],
                'article_type': Article.ArticleType.FEATURE,
                'status': Article.ArticleStatus.PUBLISHED,
                'is_featured': False,
                'is_editors_pick': True,
                'excerpt': "When public benches are engineered with intentional dividers to repel rest, and urban plazas require a commercial transaction to inhabit, the city ceases to be a commons and becomes a turnstile.",
                'content': """
<p class="lead">Walk down any newly renovated commercial concourse in London, Manhattan, or Seoul, and you will notice a peculiar absence: places to sit without an accompanying receipt.</p>

<p>The concept of the 'third space'—that vital social realm beyond the pressures of domestic labor and corporate employment—was famously articulated by sociologist Ray Oldenburg. Yet modern urban architecture has systematically designed out the preconditions for spontaneous, non-transactional human assembly.</p>

<h3>Defensive Design and the Sanitized Street</h3>
<p>Architects call it 'defensive architecture'; critics call it hostile design. Benches angled to make prolonged conversation impossible; public squares monitored by private security details; fountains replaced by ornamental spikes. The underlying premise of these spaces is that public presence is inherently suspect unless authenticated by consumer expenditure.</p>

<blockquote>"When a public bench is replaced by an espresso bar patio, citizenship is subtly converted into a subscription service."</blockquote>

<p>Across progressive European municipalities like Vienna and Barcelona, however, counter-experiments in civic commons are yielding remarkable results. By repurposing vehicular rights-of-way into pedestrian 'superblocks' with communal tables, shade canopies, and unmonitored seating, social trust metrics have surged. The city, it turns out, only requires the permission of its architecture to foster solidarity once more.</p>
""",
                'estimated_reading_time': 4,
                'views_count': 285,
                'tags': [created_tags['architecture'], created_tags['urban-planning']],
                'sources': "Civic Spaces Review, Harvard GSD; Barcelona Urban Ecology Agency; Oldenburg, R. (1989)."
            },
            {
                'title': "The Sovereign Battery: The Geopolitical Scramble to Control the Renewable Supply Chain",
                'subtitle': "Lithium refining, rare-earth magnetics, and the quiet reconfiguration of twentieth-century petro-alliances.",
                'slug': "sovereign-battery-geopolitical-scramble",
                'author': created_authors[1],
                'category': created_categories['business'],
                'article_type': Article.ArticleType.NEWS,
                'status': Article.ArticleStatus.PUBLISHED,
                'is_featured': False,
                'is_editors_pick': False,
                'excerpt': "The transition away from hydrocarbon fuels does not signify the end of resource geopolitics; it merely substitutes oil wells for lithium brines and graphite synthesizers.",
                'content': """
<p class="lead">For eight decades, global trade routes were etched along the chokepoints of crude: the Strait of Hormuz, the Malacca Gateway, the pipelines traversing Eurasian plains. Today, the chokepoints of sovereign power are chemical rather than petroleum-based.</p>

<p>In the high-altitude salt flats of the Atacama Desert and the hard-rock spodumene reserves of Western Australia, raw battery minerals are extracted at unprecedented scale. But the true leverage lies downstream: in the high-temperature chemical refining facilities where raw ore is transformed into battery-grade lithium hydroxide and cathode precursors.</p>

<h3>The Refining Monopsony</h3>
<p>Over seventy percent of global refining capacity remains concentrated in a single sovereign jurisdiction. Western initiatives like the EU Critical Raw Materials Act and the US Inflation Reduction Act represent billions in capital deployment, yet chemical engineering bottlenecks and environmental permit queues mean domestic parity remains years away.</p>

<p>As nations construct domestic supply chains, the resulting tariff barriers and sovereign subsidies are fragmenting global commerce. The era of frictionless international commodity trading is closing; the era of strategic resource mercantilism has officially arrived.</p>
""",
                'estimated_reading_time': 4,
                'views_count': 310,
                'tags': [created_tags['clean-energy'], created_tags['macroeconomics'], created_tags['global-trade']],
                'sources': "International Energy Agency Critical Minerals Review 2024; BloombergNEF Battery Cost Index."
            },
            {
                'title': "The Synthetic Classroom: Can Generative Tutors Truly Foster Independent Thought?",
                'subtitle': "Pedagogical institutes grapple with conversational models that offer effortless answers at the expense of intellectual struggle.",
                'slug': "synthetic-classroom-independent-thought",
                'author': created_authors[0],
                'category': created_categories['education'],
                'article_type': Article.ArticleType.OPINION,
                'status': Article.ArticleStatus.PUBLISHED,
                'is_featured': False,
                'is_editors_pick': True,
                'excerpt': "When every conceptual barrier can be instantly dissolved by a polite AI tutor, we risk training a generation that mistakes informational fluency for genuine cognitive mastery.",
                'content': """
<p class="lead">Education is fundamentally an encounter with friction. The agonizing pause between misunderstanding a mathematical theorem and grasping its underlying symmetry is precisely where neural synthesis occurs.</p>

<p>Today, educational startups promise the ultimate pedagogical panacea: an adaptive AI tutor attuned to every student's learning pace, available round the clock. These systems are extraordinarily patient, undeniably knowledgeable, and quietly dangerous.</p>

<p>By eradicating the discomfort of confusion, synthetic tutors inadvertently remove the crucible of cognitive resilience. When an answer is synthesized before the student has spent thirty minutes grappling with ambiguity, the illusion of comprehension is swift, but retention is paper-thin.</p>

<p>True learning demands what philosopher John Dewey called 'productive struggle.' If educational institutions simply outsource the heavy lifting of synthesis to algorithms, we will produce graduates who can query anything, but comprehend remarkably little.</p>
""",
                'estimated_reading_time': 3,
                'views_count': 195,
                'tags': [created_tags['artificial-intelligence'], created_tags['philosophy']],
                'sources': "Dewey, J. 'How We Think'; MIT Teaching Systems Lab Report on LLM Pedagogy."
            },
            {
                'title': "The Quiet Renaissance of Deep Geothermal Energy",
                'subtitle': "Advanced directional drilling pioneered by oil drillers is unlocking unlimited baseload thermal power from deep crustal rock.",
                'slug': "renaissance-deep-geothermal-energy",
                'author': created_authors[1],
                'category': created_categories['science'],
                'article_type': Article.ArticleType.NEWS,
                'status': Article.ArticleStatus.PUBLISHED,
                'is_featured': False,
                'is_editors_pick': False,
                'excerpt': "Five kilometers beneath our feet lies enough heat to power human civilization for millennia. Engineers are finally learning how to tap it safely.",
                'content': """
<p class="lead">Unlike solar panels that fall dormant at dusk, or wind turbines susceptible to calm doldrums, the Earth's crust provides constant, unyielding heat. Yet for a century, geothermal power was restricted to rare volcanic anomalies like Iceland and northern California.</p>

<p>That geographic lottery is coming to an end. By borrowing ultra-precise horizontal drilling rigs and acoustic sensor packages from the petroleum sector, next-generation geothermal companies are boring into superhot basement granite anywhere on earth, creating engineered radiators that deliver clean baseload electricity 24 hours a day.</p>
""",
                'estimated_reading_time': 3,
                'views_count': 160,
                'tags': [created_tags['clean-energy'], created_tags['climate-science']],
                'sources': "US Department of Energy Geovision Analysis; Nature Energy Vol. 9."
            },
            {
                'title': "The Art of Slow Living: Reclaiming Attention in an Attention Economy",
                'subtitle': "Philosophical notes on disconnection, paper notebooks, and resisting algorithmic hurry.",
                'slug': "art-of-slow-living-reclaiming-attention",
                'author': created_authors[2],
                'category': created_categories['lifestyle'],
                'article_type': Article.ArticleType.EDITORIAL,
                'status': Article.ArticleStatus.PUBLISHED,
                'is_featured': False,
                'is_editors_pick': False,
                'excerpt': "In a culture that measures virtue by responsiveness and velocity, deliberate slowness is the most radical form of cultural resistance.",
                'content': """
<p class="lead">Every ping on our handheld glass slabs is a commercial invoice for our finite conscious experience. To choose unresponsiveness is not neglect; it is an act of sovereign conservation.</p>

<p>Consider the notebook. It does not ping. It does not update. It invites patience, pauses, and the deliberate evolution of thought. We must reclaim our time from the algorithms designed to monetize our agitation.</p>
""",
                'estimated_reading_time': 3,
                'views_count': 142,
                'tags': [created_tags['philosophy']],
                'sources': "Kahneman, D. 'Thinking, Fast and Slow'; Seneca, 'On the Shortness of Life'."
            },
            # Pending Submission Article for Editorial Review Queue Demonstration
            {
                'title': "Neurotechnology and the Courtroom: The Looming Crisis of Cognitive Evidence",
                'subtitle': "When functional MRI scans and neural decoding algorithms enter criminal defense, who determines the boundary of memory?",
                'slug': "neurotechnology-and-the-courtroom",
                'author': created_authors[0],
                'category': created_categories['technology'],
                'article_type': Article.ArticleType.LONGFORM,
                'status': Article.ArticleStatus.SUBMITTED,  # IN REVIEW QUEUE!
                'is_featured': False,
                'is_editors_pick': False,
                'excerpt': "A groundbreaking investigative inquiry into how neural decoding technologies are creeping into legal jurisprudence before ethical boundaries are established.",
                'content': """
<p class="lead">In an appellate courtroom in Delaware this past autumn, defense counsel introduced an exhibit unlike any seen before: a high-resolution blood-oxygenation map claiming to prove their client lacked mens rea during the commission of the act.</p>

<p>While polygraphs were rightfully relegated to pseudo-science decades ago, neuroimaging paired with transformer-based neural decoding presents an entirely different challenge. When an algorithmic classifier claims an eighty-five percent probability of recognition upon presenting evidence to a suspect's visual cortex, does this constitute self-incrimination?</p>

<p>Legal scholars and neuroscientists are currently locked in fierce debate over the cognitive Fifth Amendment. Without statutory clarity from supreme judicial bodies, our fundamental notions of privacy may not survive the decade.</p>
""",
                'estimated_reading_time': 5,
                'views_count': 0,
                'tags': [created_tags['neuroscience'], created_tags['digital-privacy']],
                'sources': "Journal of Law and the Biosciences; National Institute of Neurological Disorders Review."
            },
            # Changes Requested Article
            {
                'title': "The New Silk Roads: High-Speed Rail Corridors Reshaping Central Asia",
                'subtitle': "Freight trains traversing the Eurasian steppe are shaving weeks off maritime transit.",
                'slug': "new-silk-roads-high-speed-rail",
                'author': created_authors[1],
                'category': created_categories['business'],
                'article_type': Article.ArticleType.NEWS,
                'status': Article.ArticleStatus.CHANGES_REQUESTED,
                'is_featured': False,
                'is_editors_pick': False,
                'excerpt': "From Khorgos on the Kazakh border to industrial logistics hubs in Duisburg, overland rail infrastructure is quietly challenging container shipping monopolies.",
                'content': """
<p class="lead">Container freight across the Pacific or through the Suez Canal can take thirty to forty-five days. A high-speed electric freight corridor through the Kazakh steppe delivers precision components from Shanghai to Frankfurt in just eleven days.</p>
<p>However, gauge transitions at the old Soviet border continue to require automated bogie exchange yards...</p>
""",
                'estimated_reading_time': 4,
                'views_count': 0,
                'tags': [created_tags['global-trade']],
                'sources': "Kazakhstan National Railway Telemetry; UN Transit Corridors Report."
            }
        ]

        created_articles = []
        for a_dict in sample_articles_data:
            tags_to_add = a_dict.pop('tags')
            art, created = Article.objects.get_or_create(
                slug=a_dict['slug'],
                defaults=a_dict
            )
            art.tags.set(tags_to_add)
            created_articles.append(art)

        # Add editorial review history to the changes requested article
        changes_art = Article.objects.filter(status=Article.ArticleStatus.CHANGES_REQUESTED).first()
        if changes_art:
            ArticleReview.objects.get_or_create(
                article=changes_art,
                action="CHANGES REQUESTED",
                defaults={
                    'reviewer': admin_user,
                    'feedback': "Please verify the gauge-exchange telemetry numbers with the Kazakh transit authority and expand on the environmental comparison with maritime freight."
                }
            )

        # 8. Reader Bookmarks & History
        published_stories = Article.objects.filter(status=Article.ArticleStatus.PUBLISHED)
        for reader in created_readers:
            # Bookmark first 2 published stories
            for story in published_stories[:2]:
                Bookmark.objects.get_or_create(user=reader, article=story)
                ReadingHistory.objects.get_or_create(user=reader, article=story, defaults={'progress_percent': 100})

            # Follow author 0
            AuthorFollow.objects.get_or_create(follower=reader, author=created_authors[0])

        # 9. Comments & Replies
        main_story = published_stories.first()
        if main_story:
            # Add companion small-size gallery images to main story
            gallery_data = [
                (
                    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=800&q=80",
                    "Cooling manifolds inside the high-density computing chamber in Northern Sweden.",
                    "Photo by Lars Lindqvist / INKLINE Archive",
                    1
                ),
                (
                    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80",
                    "A prototype 16-core analog neuromorphic compute die under electron microscopy.",
                    "Nordic Microelectronics Lab",
                    2
                ),
                (
                    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80",
                    "Telemetry console tracking power draw across localized inference clusters.",
                    "Field Dispatch / INKLINE Bureau",
                    3
                ),
                (
                    "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=800&q=80",
                    "Compact edge diagnostic terminal deployed at the physical perimeter.",
                    "Photo by Maya Lin",
                    4
                ),
            ]
            for img_url, cap, cred, ordr in gallery_data:
                ArticleImage.objects.get_or_create(
                    article=main_story,
                    caption=cap,
                    defaults={'image_url': img_url, 'credit': cred, 'order': ordr}
                )

            # Also seed companion images for second published story (Architecture)
            second_story = published_stories[1] if published_stories.count() > 1 else None
            if second_story:
                arch_gallery = [
                    (
                        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
                        "A privatized commercial atrium in central London with restricted seating.",
                        "Elena Rostova / Archival Dispatch",
                        1
                    ),
                    (
                        "https://images.unsplash.com/photo-1477959858617-67f30bc75b82?auto=format&fit=crop&w=800&q=80",
                        "Pedestrian superblock experiment in Barcelona restoring public assembly.",
                        "Civic Commons Project",
                        2
                    ),
                    (
                        "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80",
                        "Community gatherers sharing unmonitored civic tables at dusk.",
                        "Photo by Elena Rostova",
                        3
                    ),
                ]
                for img_url, cap, cred, ordr in arch_gallery:
                    ArticleImage.objects.get_or_create(
                        article=second_story,
                        caption=cap,
                        defaults={'image_url': img_url, 'credit': cred, 'order': ordr}
                    )
        if main_story:
            c1, _ = Comment.objects.get_or_create(
                article=main_story,
                user=created_readers[0],
                content="Extraordinary reporting, Maya. The analysis regarding thermodynamic constraints in data centers aligns perfectly with what hardware teams are seeing in the semiconductor sector.",
                defaults={'is_approved': True}
            )
            # Reply from author
            Comment.objects.get_or_create(
                article=main_story,
                user=created_authors[0],
                parent=c1,
                content="Thank you Clara. That bottleneck is precisely why photonic interconnects and analog edge chips are seeing such massive venture backing right now.",
                defaults={'is_approved': True}
            )
            Comment.objects.get_or_create(
                article=main_story,
                user=created_readers[1],
                content="Will edge models ever be capable of the deep multi-step deduction seen in 70B+ parameter clusters, or are we settling for narrower domain intelligence?",
                defaults={'is_approved': True}
            )

        # 10. Article Views Telemetry (simulate past 7-day distribution for Chart.js)
        now = timezone.now()
        for i in range(7):
            day_time = now - timedelta(days=i)
            # Create a cluster of view logs for each day
            for _ in range(random.randint(6, 18)):
                ArticleView.objects.create(
                    article=main_story,
                    user=random.choice(created_readers),
                    ip_address="127.0.0.1",
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    session_key=f"sample-session-{i}",
                )
                # Manually adjust timestamp
                ArticleView.objects.filter(pk=ArticleView.objects.first().pk).update(timestamp=day_time)

        self.stdout.write(self.style.SUCCESS(
            "\nSuccessfully loaded INKLINE demonstration publishing dataset!\n"
            "----------------------------------------------------------\n"
            "ACCOUNTS CREATED:\n"
            "1. Administrator : username='admin', password='AdminPassword123!'\n"
            "2. Author 1      : username='maya_lin', password='AuthorPassword123!'\n"
            "3. Author 2      : username='julian_sterling', password='AuthorPassword123!'\n"
            "4. Reader 1      : username='clara_b', password='ReaderPassword123!'\n"
            "----------------------------------------------------------\n"
        ))
