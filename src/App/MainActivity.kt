package com.example.digitaltwinflowchart

import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.widget.Button
import android.widget.FrameLayout
import androidx.appcompat.app.AppCompatActivity
import androidx.activity.result.contract.ActivityResultContracts
import org.json.JSONArray
import org.json.JSONObject
import java.io.InputStream
import java.util.Locale
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

class MainActivity : AppCompatActivity(), TextToSpeech.OnInitListener {

    private lateinit var tts: TextToSpeech
    private lateinit var canvas: FrameLayout

    // --- NEW: TRACK THE USER'S EXPERTISE LEVEL ---
    // 0 = Principiante (Everything: Type, Content, Directions)
    // 1 = Intermedio (Type and Content only)
    // 2 = Esperto (Content only)
    //TODO maybe 3 = Full explanation of what is the purpose of this node type
    private var expertiseLevel = 0

    // ========================================================================
    // 1. FILE HANDLING & INTENTS
    // ========================================================================

    // File Picker to change Flowchart dynamically
    private val pickFileLauncher = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            try {
                val inputStream = contentResolver.openInputStream(uri)
                val newJsonString = inputStream?.bufferedReader().use { it?.readText() }

                if (newJsonString != null) {
                    println("Loaded new JSON from user!")
                    drawFlowchart(newJsonString)
                    tts.speak("Diagramma caricato con successo", TextToSpeech.QUEUE_FLUSH, null, "")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                tts.speak("Errore durante il caricamento del file", TextToSpeech.QUEUE_FLUSH, null, "")
            }
        }
    }

    // ========================================================================
    // 2. LIFECYCLE & INITIALIZATION
    // ========================================================================

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Setup Screen & UI
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        hideSystemBars()
        setContentView(R.layout.activity_main)
        canvas = findViewById(R.id.canvas_layout)

        // Setup Text-To-Speech
        tts = TextToSpeech(this, this)

        // Set up the hidden File Picker trigger (Long Press on background)
        canvas.setOnLongClickListener {
            tts.speak("Seleziona un diagramma", TextToSpeech.QUEUE_FLUSH, null, "")
            pickFileLauncher.launch("*/*")
            true
        }

        // Load Default Diagram on Startup
        try {
            val inputStream: InputStream = assets.open("output_coordinates.json")
            val defaultJsonString = inputStream.bufferedReader().use { it.readText() }
            drawFlowchart(defaultJsonString)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    // ========================================================================
    // 3. CORE LAYOUT ENGINE
    // ========================================================================

    private fun drawFlowchart(jsonString: String) {
        // --- STEP A: PREPARE CANVAS & PARSE DATA ---
        canvas.removeAllViews()

        val trimmedString = jsonString.trim()
        val jsonObject = if (trimmedString.startsWith("[")) {
            val jsonArray = JSONArray(trimmedString)
            if (jsonArray.length() > 0) jsonArray.getJSONObject(0) else JSONObject()
        } else {
            JSONObject(trimmedString)
        }

        val childrenArray = jsonObject.getJSONArray("children")
        val edgesArray = jsonObject.optJSONArray("edges")


        // --- STEP B: PHYSICAL HARDWARE CONSTANTS ---
        val displayMetrics = resources.displayMetrics
        fun mmToPixelsX(mm: Float): Int = ((mm / 25.4f) * displayMetrics.xdpi).toInt()
        fun mmToPixelsY(mm: Float): Int = ((mm / 25.4f) * displayMetrics.ydpi).toInt()

        // TODO: Switch to JSON dynamic size when ready
        val baseWidthMM = 135f
        val baseHeightMM = 217f

        val blockSizeMM = 17f
        val marginXMM = 5f
        val marginYMM = 5f
        val safeMarginX = marginXMM + (blockSizeMM / 2f)
        val safeMarginY = marginYMM + (blockSizeMM / 2f)


        // --- STEP C: CALCULATE BOUNDING BOX (MIN / MAX REACH) ---
        var minX = Float.MAX_VALUE; var maxX = -Float.MAX_VALUE
        var minY = Float.MAX_VALUE; var maxY = -Float.MAX_VALUE

        // 1. Check Node Boundaries
        for (i in 0 until childrenArray.length()) {
            val node = childrenArray.getJSONObject(i)
            val centerX = node.getDouble("x").toFloat() + (node.getDouble("width").toFloat() / 2f)
            val centerY = -(node.getDouble("y").toFloat() + (node.getDouble("height").toFloat() / 2f))

            minX = min(minX, centerX); maxX = max(maxX, centerX)
            minY = min(minY, centerY); maxY = max(maxY, centerY)
        }

        // 2. Check Edge (Wire) Boundaries
        if (edgesArray != null) {
            for (i in 0 until edgesArray.length()) {
                val sections = edgesArray.getJSONObject(i).optJSONArray("sections") ?: continue
                for (j in 0 until sections.length()) {
                    val bendPoints = sections.getJSONObject(j).optJSONArray("bendPoints") ?: continue
                    for (k in 0 until bendPoints.length()) {
                        val bpX = bendPoints.getJSONObject(k).getDouble("x").toFloat()
                        val bpY = -bendPoints.getJSONObject(k).getDouble("y").toFloat()
                        minX = min(minX, bpX); maxX = max(maxX, bpX)
                        minY = min(minY, bpY); maxY = max(maxY, bpY)
                    }
                }
            }
        }

        // 3. Apply Main Spine Centering
        val firstNode = childrenArray.getJSONObject(0)
        val spineX = firstNode.getDouble("x").toFloat() + (firstNode.getDouble("width").toFloat() / 2f)
        val maxReachX = max(abs(maxX - spineX), abs(minX - spineX))

        minX = spineX - maxReachX
        maxX = spineX + maxReachX


        // --- STEP D: CALCULATE FINAL SCALE AND OFFSETS ---
        val gridSpacing = min(
            (baseWidthMM - (safeMarginX * 2)) / max(1f, maxX - minX),
            (baseHeightMM - (safeMarginY * 2)) / max(1f, maxY - minY)
        )

        val xOffsetMM = (baseWidthMM / 2f) - (((minX + maxX) / 2f) * gridSpacing)
        val yOffsetMM = (baseHeightMM / 2f) - (((minY + maxY) / 2f) * gridSpacing)


        // --- STEP E: RENDER FLOWCHART NODES ---
        val playMM = 8.0f // Safety margin for button overlap
        val drawnSizeMM = blockSizeMM + playMM

        for (i in 0 until childrenArray.length()) {
            val node = childrenArray.getJSONObject(i)
            val nodeId = node.optString("id")
            val nX = node.getDouble("x").toFloat()
            val nY = node.getDouble("y").toFloat()
            val nWidth = node.getDouble("width").toFloat()
            val nHeight = node.getDouble("height").toFloat()

            // Calculate Physical Placement
            val centerX = nX + (nWidth / 2f)
            val centerY = -(nY + (nHeight / 2f))
            val physicalX_MM = (centerX * gridSpacing) + xOffsetMM
            val physicalY_MM = baseHeightMM - ((centerY * gridSpacing) + yOffsetMM) // Android Y-Flip

            val pixelX = mmToPixelsX(physicalX_MM - (drawnSizeMM / 2f))
            val pixelY = mmToPixelsY(physicalY_MM - (drawnSizeMM / 2f))
            val pixelWidth = mmToPixelsX(drawnSizeMM)
            val pixelHeight = mmToPixelsY(drawnSizeMM)

            // Get Text & Shape Data
            val baseText = node.optJSONArray("labels")?.getJSONObject(0)?.optString("text") ?: "Node"
            val shapeType = node.optString("myCustomShape", "square")

            // Create UI Button
            val button = Button(this@MainActivity).apply {
                text = baseText
                isAllCaps = false
                androidx.core.widget.TextViewCompat.setAutoSizeTextTypeWithDefaults(
                    this, androidx.core.widget.TextViewCompat.AUTO_SIZE_TEXT_TYPE_UNIFORM
                )

                // Force Yellow Circle Shape
                background = android.graphics.drawable.GradientDrawable().apply {
                    setColor(android.graphics.Color.parseColor("#FFFF00"))
                    shape = android.graphics.drawable.GradientDrawable.OVAL
                }

                // --- CHANGED: DYNAMIC TTS GENERATION ---
                // We generate the text exactly when clicked, passing the current expertiseLevel!
                setOnClickListener {
                    val spokenText = buildNodeSpokenText(nodeId, baseText, shapeType, edgesArray, expertiseLevel)
                    tts.speak(spokenText, TextToSpeech.QUEUE_FLUSH, null, "")
                }
            }

            // Add to Canvas
            val params = FrameLayout.LayoutParams(pixelWidth, pixelHeight).apply {
                leftMargin = pixelX
                topMargin = pixelY
            }
            canvas.addView(button, params)
        }


        // --- STEP F: RENDER MENU BUTTON ---
        val menuRadiusMM = 8f
        val menuOffsetMM = 5f
        val menuSizeMM = menuRadiusMM * 2f

        // Center relative to Android's top-left origin (0,0)
        val menuCenterX_MM = baseWidthMM - menuRadiusMM - menuOffsetMM
        val menuCenterY_MM = menuRadiusMM + menuOffsetMM

        val menuPixelX = mmToPixelsX(menuCenterX_MM - (menuSizeMM / 2f))
        val menuPixelY = mmToPixelsY(menuCenterY_MM - (menuSizeMM / 2f))

        val menuButton = Button(this@MainActivity).apply {
            text = "Menu"
            isAllCaps = false
            androidx.core.widget.TextViewCompat.setAutoSizeTextTypeWithDefaults(
                this, androidx.core.widget.TextViewCompat.AUTO_SIZE_TEXT_TYPE_UNIFORM
            )
            // Orange Square
            background = android.graphics.drawable.GradientDrawable().apply {
                setColor(android.graphics.Color.parseColor("#FF9800"))
                shape = android.graphics.drawable.GradientDrawable.RECTANGLE
            }

            // --- CHANGED: CYCLIC MENU ---
            // Short Tap cycles the expertise level
            setOnClickListener {
                expertiseLevel = (expertiseLevel + 1) % 3
                val levelName = when(expertiseLevel) {
                    0 -> "Principiante"
                    1 -> "Intermedio"
                    2 -> "Esperto"
                    else -> ""
                }
                tts.speak("Livello $levelName", TextToSpeech.QUEUE_FLUSH, null, "")
            }

            // --- ADDED: LONG CLICK FOR FILE PICKER ---
            // Long Tap opens the file explorer
            setOnLongClickListener {
                tts.speak("Seleziona un diagramma", TextToSpeech.QUEUE_FLUSH, null, "")
                pickFileLauncher.launch("*/*")
                true // returning true tells Android the long-click was consumed successfully
            }
        }

        val menuParams = FrameLayout.LayoutParams(mmToPixelsX(menuSizeMM), mmToPixelsY(menuSizeMM)).apply {
            leftMargin = menuPixelX
            topMargin = menuPixelY
        }
        canvas.addView(menuButton, menuParams)
    }

    // ========================================================================
    // 4. LOGIC HELPERS & UTILITIES
    // ========================================================================

    /**
     * Builds the string of text that the Text-To-Speech engine will read aloud.
     * Output dynamically changes based on the user's expertise level.
     */
    private fun buildNodeSpokenText(nodeId: String, baseText: String, shapeType: String, edgesArray: JSONArray?, level: Int): String {

        // 1. Clean up math logic into spoken words (Happens for ALL levels)
        val cleanText = baseText.replace("<=", " minore o uguale di ")
            .replace(">=", " maggiore o uguale di ")
            .replace("==", " uguale a ")
            .replace("!=", " diverso da ")
            .replace("<", " minore di ")
            .replace(">", " maggiore di ")
            .replace("++", " più uno ")
            .replace("--", " meno uno ")
            .replace("+", " più ")
            .replace("-", " meno ")
            .replace("=", " uguale a ")

        // Level 2 (Esperto): The user only wants to hear the code/content. Stop here.
        if (level == 2) {
            return cleanText
        }

        // 2. Identify the shape (Needed for Novice)
        val logicalMeaning = when(shapeType) {
            "circle" -> if (baseText.contains("START", ignoreCase = true)) "Nodo Inizio" else "Nodo Fine"
            "diamond" -> "Nodo Decisione"
            "trapezoid" -> "Nodo Input/Output"
            else -> "Nodo Processo"
        }

        // 3. Identify the Edges.
        var routingText = " "
        if (edgesArray != null) {
            for (j in 0 until edgesArray.length()) {
                val edge = edgesArray.getJSONObject(j)
                if (edge.optString("source") == nodeId) {
                    val edgeLabel = edge.optJSONArray("labels")?.getJSONObject(0)?.optString("text") ?: ""
                    var direction = ""

                    val sections = edge.optJSONArray("sections")
                    if (sections != null && sections.length() > 0) {
                        val section = sections.getJSONObject(0)
                        val startX = section.getJSONObject("startPoint").getDouble("x")
                        val startY = section.getJSONObject("startPoint").getDouble("y")

                        val bendPoints = section.optJSONArray("bendPoints")
                        val nextPoint = if (bendPoints != null && bendPoints.length() > 0) {
                            bendPoints.getJSONObject(0)
                        } else {
                            section.getJSONObject("endPoint")
                        }

                        val dx = nextPoint.getDouble("x") - startX
                        val dy = nextPoint.getDouble("y") - startY

                        direction = if (abs(dx) > abs(dy)) {
                            if (dx > 0) " a destra " else "a sinistra "
                        } else {
                            if (dy > 0) "giù " else "su "
                        }
                    }

                    routingText += if (edgeLabel.isNotEmpty()) " Arco $edgeLabel va $direction. " else " Arco va $direction. "
                }
            }
        }


        // Level 1 (Intermedio): Read the shape content and edges. Stop here.
        if (level == 1) {
            return "$cleanText. $routingText."
        }


        return if (routingText.trim().isNotEmpty()) "$logicalMeaning. $cleanText... ${routingText.trim()}" else "$logicalMeaning. $cleanText."



    }

    // ========================================================================
    // 5. SYSTEM SETTINGS
    // ========================================================================

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            val result = tts.setLanguage(Locale.ITALY)
            if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                println("TTS Error: Italian language pack missing.")
            } else {
                tts.setSpeechRate(1.5f)
                tts.setPitch(0.9f)
            }
        }
    }

    override fun onDestroy() {
        if (::tts.isInitialized) { tts.stop(); tts.shutdown() }
        super.onDestroy()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) hideSystemBars()
    }

    private fun hideSystemBars() {
        androidx.core.view.WindowCompat.setDecorFitsSystemWindows(window, false)
        val windowInsetsController = androidx.core.view.WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.hide(androidx.core.view.WindowInsetsCompat.Type.systemBars())
        windowInsetsController.systemBarsBehavior = androidx.core.view.WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
    }
}